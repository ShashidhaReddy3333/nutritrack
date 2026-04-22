from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserProfile
from app.schemas.user import ProfileCreate, ProfileUpdate, ProfileOut, DailyTargets
from app.services.nutrition_calc import calculate_targets
from app.api.deps import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


def _build_profile_out(profile: UserProfile) -> ProfileOut:
    """Attach calculated_targets to the outgoing schema."""
    calculated = calculate_targets(
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
        age=profile.age,
        sex=profile.sex,
        activity_level=profile.activity_level,
        goal=profile.goal,
    )
    out = ProfileOut.model_validate(profile)
    out.calculated_targets = calculated
    return out


@router.post("", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.profile:
        raise HTTPException(status_code=400, detail="Profile already exists. Use PATCH to update.")

    # Persist override targets if provided
    override_json = payload.override_targets.model_dump() if payload.override_targets else None
    body_composition_json = payload.body_composition_report.model_dump() if payload.body_composition_report else None

    profile = UserProfile(
        user_id=current_user.id,
        age=payload.age,
        sex=payload.sex,
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
        activity_level=payload.activity_level,
        goal=payload.goal,
        timezone=payload.timezone,
        daily_targets_json=override_json,
        body_composition_json=body_composition_json,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _build_profile_out(profile)


@router.get("", response_model=ProfileOut)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _build_profile_out(current_user.profile)


@router.patch("", response_model=ProfileOut)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Create one first.")

    update_data = payload.model_dump(exclude_unset=True)
    override_targets_present = "override_targets" in update_data
    body_report_present = "body_composition_report" in update_data
    override_targets = update_data.pop("override_targets", None)
    body_composition_report = update_data.pop("body_composition_report", None)

    for field, value in update_data.items():
        setattr(profile, field, value)

    if override_targets_present:
        # Explicit None clears the override; a DailyTargets object sets it (Issue 26)
        profile.daily_targets_json = (
            override_targets.model_dump() if override_targets is not None else None
        )
    if body_report_present:
        profile.body_composition_json = (
            body_composition_report.model_dump() if body_composition_report is not None else None
        )

    db.commit()
    db.refresh(profile)
    return _build_profile_out(profile)


@router.get("/targets", response_model=DailyTargets)
def get_targets(
    current_user: User = Depends(get_current_user),
):
    """Returns effective daily targets: override if set, else calculated."""
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.daily_targets_json:
        return DailyTargets(**profile.daily_targets_json)

    return calculate_targets(
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
        age=profile.age,
        sex=profile.sex,
        activity_level=profile.activity_level,
        goal=profile.goal,
    )
