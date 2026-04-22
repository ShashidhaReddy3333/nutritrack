import hashlib
import logging
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.refresh_token import PasswordResetToken, RefreshToken
from app.models.user import User
from app.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    SessionResponse,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Cookie names
ACCESS_COOKIE = "nutritrack_access"
REFRESH_COOKIE = "nutritrack_refresh"

_COOKIE_KWARGS = dict(
    httponly=True,
    secure=settings.COOKIE_SECURE,
    samesite=settings.COOKIE_SAMESITE,
    path="/",
)


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **_COOKIE_KWARGS,
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        **_COOKIE_KWARGS,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


def _store_refresh_token(db: Session, user_id, token: str) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires))
    db.commit()


def _cleanup_expired_refresh_tokens(db: Session) -> None:
    deleted = db.query(RefreshToken).filter(
        RefreshToken.expires_at < datetime.now(timezone.utc)
    ).delete(synchronize_session=False)
    if deleted:
        db.commit()


def _send_password_reset_email(email: str, reset_url: str) -> None:
    if not settings.SMTP_HOST:
        if settings.APP_ENV == "development":
            logger.info("Password reset link for %s: %s", email, reset_url)
        else:
            logger.error("SMTP_HOST is not configured; password reset email was not sent")
        return

    message = EmailMessage()
    message["Subject"] = "Reset your NutriTrack password"
    message["From"] = settings.SMTP_FROM
    message["To"] = email
    message.set_content(
        "Use this link to reset your NutriTrack password. "
        "It expires in 30 minutes:\n\n"
        f"{reset_url}\n"
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)


def _session_response(user: User) -> SessionResponse:
    return SessionResponse(user=UserOut.model_validate(user))


@router.post("/register", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
def register(request: Request, payload: UserCreate, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        # Generic message to prevent email enumeration (Issue 20)
        raise HTTPException(
            status_code=400,
            detail="Registration failed. Please check your details and try again.",
        )

    user = User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        privacy_consent_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token()
    _store_refresh_token(db, user.id, refresh_token)
    _set_auth_cookies(response, access_token, refresh_token)

    return _session_response(user)


@router.post("/login", response_model=SessionResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token()
    _store_refresh_token(db, user.id, refresh_token)
    _set_auth_cookies(response, access_token, refresh_token)

    return _session_response(user)


@router.post("/refresh", response_model=SessionResponse)
def refresh_token_endpoint(request: Request, response: Response, db: Session = Depends(get_db)):
    """Exchange a valid refresh token cookie for a new access+refresh token pair."""
    _cleanup_expired_refresh_tokens(db)
    raw_token = request.cookies.get(REFRESH_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    record = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > now,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    # Rotate: revoke old, issue new
    record.revoked = True
    new_access = create_access_token(str(record.user_id))
    new_refresh = create_refresh_token()
    _store_refresh_token(db, record.user_id, new_refresh)
    db.commit()

    _set_auth_cookies(response, new_access, new_refresh)
    return _session_response(record.user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Revoke the refresh token and clear auth cookies."""
    raw_token = request.cookies.get(REFRESH_COOKIE)
    if raw_token:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if record:
            record.revoked = True
            db.commit()
    _clear_auth_cookies(response)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("3/minute")
def forgot_password(request: Request, payload: "ForgotPasswordRequest", db: Session = Depends(get_db)):
    """Initiate password reset. Always returns 202 to prevent email enumeration."""
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,  # noqa: E712
        ).update({"used": True}, synchronize_session=False)

        reset_token = create_refresh_token()
        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
        expires = datetime.now(timezone.utc) + timedelta(minutes=30)
        db.add(PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires))
        db.commit()

        reset_url = f"{settings.PUBLIC_APP_URL.rstrip('/')}/reset-password?token={reset_token}"
        try:
            _send_password_reset_email(user.email, reset_url)
        except Exception as exc:
            logger.error("Password reset email delivery failed for user %s: %s", user.id, exc, exc_info=True)
    # Always return 202 regardless of whether the email exists
    return {"detail": "If that email is registered, a password reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: "ResetPasswordRequest", db: Session = Depends(get_db)):
    """Complete password reset with a valid token."""
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False,  # noqa: E712
            PasswordResetToken.expires_at > now,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user.password_hash = get_password_hash(payload.new_password)
    record.used = True
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update(
        {"revoked": True},
        synchronize_session=False,
    )
    db.commit()
    return {"detail": "Password reset complete. You can now sign in."}
