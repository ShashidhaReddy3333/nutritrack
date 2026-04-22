import asyncio
import uuid
import logging
from datetime import datetime, date, timedelta, timezone as dt_timezone
from typing import Optional, List
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.models.meal import MealEntry, MealItem, MealType
from app.models.product import Product
from app.schemas.meal import (
    ParseRequest, ParseResponse, ParsedItemWithCandidates,
    CandidateProduct, ParsedItem,
    MealEntryCreate, MealEntryUpdate, MealEntryOut, MealItemOut, ResolvedNutrients,
)
from app.services.meal_parser import parse_meal_text
from app.services.embeddings import semantic_search
from app.services.unit_conversion import scale_nutrients
from app.api.deps import get_current_user

router = APIRouter(prefix="/meals", tags=["meals"])
logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.45


def _day_range(d: date):
    """Return (start, end) datetimes for a full calendar day (UTC). Fixes Issue 16."""
    start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=dt_timezone.utc)
    end = start + timedelta(days=1)  # exclusive upper bound — no more 23:59:59 cutoff
    return start, end


def _resolve_timezone(current_user: User, timezone_name: Optional[str]) -> ZoneInfo:
    name = timezone_name or getattr(getattr(current_user, "profile", None), "timezone", None) or "UTC"
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(status_code=400, detail="Invalid timezone") from exc


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=dt_timezone.utc)
    return value.astimezone(dt_timezone.utc)


def _local_day_range(d: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    """Return UTC datetimes covering one user-local calendar day."""
    start_local = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(dt_timezone.utc), end_local.astimezone(dt_timezone.utc)


def _local_today(tz: ZoneInfo) -> date:
    return datetime.now(tz).date()


def _entry_day_key(logged_at: datetime, tz: ZoneInfo) -> str:
    return _to_utc(logged_at).astimezone(tz).date().isoformat()


# ── Parse (preview before save) ───────────────────────────────────────────────

@router.post("/parse", response_model=ParseResponse)
@limiter.limit("10/minute")
async def parse_meal(
    request: Request,
    payload: ParseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        parsed_items = await parse_meal_text(payload.raw_text)
    except Exception as exc:
        logger.error("LLM meal-parse error for user %s: %s", current_user.id, exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="AI processing failed. Please try again or add the meal manually.",
        )

    results: list[ParsedItemWithCandidates] = []

    for item_data in parsed_items:
        item_name = item_data.get("item", "")
        quantity = float(item_data.get("quantity", 1))
        unit = str(item_data.get("unit", "serving"))

        sem_results = await asyncio.to_thread(semantic_search, item_name, str(current_user.id), 5)

        keyword_hits = (
            db.query(Product)
            .filter(
                Product.user_id == current_user.id,
                Product.is_deleted == False,  # noqa: E712
                Product.name.ilike(f"%{item_name}%"),
            )
            .limit(5)
            .all()
        )

        product_scores: dict[str, float] = {r["product_id"]: r["score"] for r in sem_results}
        for p in keyword_hits:
            pid = str(p.id)
            if pid not in product_scores:
                product_scores[pid] = 0.5

        if not product_scores:
            candidates = []
        else:
            products = (
                db.query(Product)
                .filter(
                    Product.id.in_([uuid.UUID(pid) for pid in product_scores]),
                    Product.user_id == current_user.id,
                    Product.is_deleted == False,  # noqa: E712
                )
                .all()
            )
            candidates = sorted(
                [
                    CandidateProduct(
                        product_id=p.id,
                        name=p.name,
                        brand=p.brand,
                        score=product_scores[str(p.id)],
                        serving_size_g=p.serving_size_g,
                        calories_per_serving=p.calories,
                    )
                    for p in products
                ],
                key=lambda c: -c.score,
            )[:3]

        best_score = candidates[0].score if candidates else 0.0
        needs_confirmation = best_score < CONFIDENCE_THRESHOLD

        results.append(
            ParsedItemWithCandidates(
                parsed=ParsedItem(item=item_name, quantity=quantity, unit=unit),
                candidates=candidates,
                needs_confirmation=needs_confirmation,
            )
        )

    return ParseResponse(items=results)


# ── Log a meal entry ───────────────────────────────────────────────────────────

@router.post("", response_model=MealEntryOut, status_code=status.HTTP_201_CREATED)
def create_meal_entry(
    payload: MealEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = MealEntry(
        user_id=current_user.id,
        meal_type=payload.meal_type,
        logged_at=_to_utc(payload.logged_at) if payload.logged_at else datetime.now(dt_timezone.utc),
        raw_text=payload.raw_text,
        parsed_items_json=[i.model_dump(mode="json") for i in payload.items],
    )
    db.add(entry)
    db.flush()
    _replace_entry_items(entry, payload.items, db, current_user)

    db.commit()
    db.refresh(entry)
    return _entry_out(entry, db)


@router.patch("/{entry_id}", response_model=MealEntryOut)
def update_meal_entry(
    entry_id: uuid.UUID,
    payload: MealEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(MealEntry).filter(
        MealEntry.id == entry_id,
        MealEntry.user_id == current_user.id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Meal entry not found")

    entry.meal_type = payload.meal_type
    entry.raw_text = payload.raw_text
    if payload.logged_at is not None:
        entry.logged_at = _to_utc(payload.logged_at)
    entry.parsed_items_json = [i.model_dump(mode="json") for i in payload.items]

    _replace_entry_items(entry, payload.items, db, current_user)

    db.commit()
    db.refresh(entry)
    return _entry_out(entry, db)


# ── List / get / delete ───────────────────────────────────────────────────────

@router.get("", response_model=List[MealEntryOut])
def list_meal_entries(
    date_filter: Optional[str] = None,
    search: Optional[str] = Query(default=None, min_length=1, max_length=120),
    timezone_name: Optional[str] = Query(default=None, alias="timezone"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tz = _resolve_timezone(current_user, timezone_name)
    # Eager-load items and their products to avoid N+1 (Issue 11)
    q = (
        db.query(MealEntry)
        .options(joinedload(MealEntry.items).joinedload(MealItem.product))
        .filter(MealEntry.user_id == current_user.id)
    )

    if search:
        q = q.filter(MealEntry.raw_text.ilike(f"%{search.strip()}%"))

    if date_filter:
        try:
            d = date.fromisoformat(date_filter)
            start, end = _local_day_range(d, tz)
            q = q.filter(MealEntry.logged_at >= start, MealEntry.logged_at < end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    entries = q.order_by(MealEntry.logged_at.desc()).offset(skip).limit(limit).all()
    return [_entry_out(e, db) for e in entries]


@router.get("/today", response_model=List[MealEntryOut])
def get_today_meals(
    timezone_name: Optional[str] = Query(default=None, alias="timezone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tz = _resolve_timezone(current_user, timezone_name)
    start, end = _local_day_range(_local_today(tz), tz)
    entries = (
        db.query(MealEntry)
        .options(joinedload(MealEntry.items).joinedload(MealItem.product))
        .filter(
            MealEntry.user_id == current_user.id,
            MealEntry.logged_at >= start,
            MealEntry.logged_at < end,
        )
        .order_by(MealEntry.logged_at)
        .all()
    )
    return [_entry_out(e, db) for e in entries]


@router.get("/daily-totals", response_model=ResolvedNutrients)
def get_daily_totals(
    date_filter: Optional[str] = None,
    timezone_name: Optional[str] = Query(default=None, alias="timezone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tz = _resolve_timezone(current_user, timezone_name)
    if date_filter:
        try:
            d = date.fromisoformat(date_filter)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    else:
        d = _local_today(tz)

    start, end = _local_day_range(d, tz)
    entries = (
        db.query(MealEntry)
        .options(joinedload(MealEntry.items))
        .filter(
            MealEntry.user_id == current_user.id,
            MealEntry.logged_at >= start,
            MealEntry.logged_at < end,
        )
        .all()
    )
    return _sum_entries(entries)


@router.get("/weekly-totals")
def get_weekly_totals(
    timezone_name: Optional[str] = Query(default=None, alias="timezone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns daily totals for the last 7 days using a single aggregated DB query (Issue 12).
    """
    tz = _resolve_timezone(current_user, timezone_name)
    today = _local_today(tz)
    seven_days_ago, _ = _local_day_range(today - timedelta(days=6), tz)
    _, tomorrow = _local_day_range(today, tz)

    # Fetch all entries + items for the 7-day window in one query
    entries = (
        db.query(MealEntry)
        .options(joinedload(MealEntry.items))
        .filter(
            MealEntry.user_id == current_user.id,
            MealEntry.logged_at >= seven_days_ago,
            MealEntry.logged_at < tomorrow,
        )
        .all()
    )

    # Partition in Python — much faster than 7 separate queries
    daily: dict[str, dict] = {}
    for i in range(7):
        d = today - timedelta(days=6 - i)
        daily[d.isoformat()] = {
            "date": d.isoformat(),
            "calories": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0,
            "sugar_g": 0.0,
            "fiber_g": 0.0,
            "sodium_mg": 0.0,
        }

    for entry in entries:
        if entry.logged_at:
            day_key = _entry_day_key(entry.logged_at, tz)
            if day_key in daily:
                for item in entry.items:
                    n = item.resolved_nutrients_json or {}
                    for k in ("calories", "protein_g", "carbs_g", "fat_g", "sugar_g", "fiber_g", "sodium_mg"):
                        daily[day_key][k] += n.get(k, 0) or 0

    result = []
    for row in daily.values():
        result.append({k: round(v, 1) if isinstance(v, float) else v for k, v in row.items()})

    return result


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal_entry(
    entry_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(MealEntry).filter(
        MealEntry.id == entry_id, MealEntry.user_id == current_user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Meal entry not found")
    db.delete(entry)
    db.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _entry_out(entry: MealEntry, db: Session) -> MealEntryOut:
    """Build MealEntryOut. Items + products are eagerly loaded — no N+1 (Issue 11)."""
    items_out = []
    for item in entry.items:
        # product is already joined via joinedload — no extra query
        product_name = item.product.name if item.product else None
        product_brand = item.product.brand if item.product else None
        product_name = product_name or item.product_name_snapshot
        product_brand = product_brand or item.product_brand_snapshot
        items_out.append(MealItemOut(
            id=item.id,
            product_id=item.product_id,
            product_name=product_name,
            product_brand=product_brand,
            quantity=item.quantity,
            unit=item.unit,
            resolved_nutrients_json=item.resolved_nutrients_json,
            confidence_score=item.confidence_score,
        ))

    total = _sum_items(entry.items)
    return MealEntryOut(
        id=entry.id,
        user_id=entry.user_id,
        meal_type=entry.meal_type,
        logged_at=entry.logged_at,
        raw_text=entry.raw_text,
        items=items_out,
        total_nutrients=total,
    )


def _replace_entry_items(
    entry: MealEntry,
    items: list,
    db: Session,
    current_user: User,
) -> None:
    """
    Validate all products FIRST, then clear+replace items.
    This prevents a partial-delete if a product_id is not found (Issue 27).
    """
    # Step 1: validate all product IDs before touching existing items
    product_map: dict[str, Product] = {}
    for item_in in items:
        pid_str = str(item_in.product_id)
        if pid_str not in product_map:
            product = db.query(Product).filter(
                Product.id == item_in.product_id,
                Product.user_id == current_user.id,
                Product.is_deleted == False,  # noqa: E712
            ).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item_in.product_id} not found")
            product_map[pid_str] = product

    # Step 2: safe to clear now that all products are confirmed
    entry.items.clear()
    db.flush()

    # Step 3: add new items
    for item_in in items:
        product = product_map[str(item_in.product_id)]
        nutrients = scale_nutrients(
            {
                "serving_size_g": product.serving_size_g,
                "serving_quantity": product.serving_quantity,
                "serving_unit": product.serving_unit,
                "calories": product.calories,
                "protein_g": product.protein_g,
                "carbs_g": product.carbs_g,
                "fat_g": product.fat_g,
                "sugar_g": product.sugar_g,
                "fiber_g": product.fiber_g,
                "sodium_mg": product.sodium_mg,
            },
            item_in.quantity,
            item_in.unit,
        )
        db.add(MealItem(
            meal_entry_id=entry.id,
            product_id=item_in.product_id,
            product_name_snapshot=product.name,
            product_brand_snapshot=product.brand,
            quantity=item_in.quantity,
            unit=item_in.unit,
            resolved_nutrients_json=nutrients,
            confidence_score=1.0,
        ))


def _sum_items(items) -> ResolvedNutrients:
    """Unified nutrient summer — used by both _entry_out and _sum_entries (Issue 25)."""
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0,
              "sugar_g": 0.0, "fiber_g": 0.0, "sodium_mg": 0.0}
    for item in items:
        n = item.resolved_nutrients_json or {}
        for k in totals:
            totals[k] += n.get(k, 0) or 0
    return ResolvedNutrients(**{k: round(v, 1) for k, v in totals.items()})


def _sum_entries(entries: list) -> ResolvedNutrients:
    """Sum nutrients across multiple entries — delegates to _sum_items (Issue 25)."""
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0,
              "sugar_g": 0.0, "fiber_g": 0.0, "sodium_mg": 0.0}
    for entry in entries:
        partial = _sum_items(entry.items)
        for k in totals:
            totals[k] += getattr(partial, k)
    return ResolvedNutrients(**{k: round(v, 1) for k, v in totals.items()})
