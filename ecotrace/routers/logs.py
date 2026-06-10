"""
Emission logs CRUD router.

- POST   /logs          → Create a new emission log entry
- GET    /logs?days=7   → Get recent logs with CO₂e totals
- DELETE /logs/{id}     → Remove a log entry
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from database import get_session
from models import (
    CATEGORY_UNITS,
    EMISSION_FACTORS,
    VALID_CATEGORIES,
    VALID_SUB_TYPES,
    EmissionLog,
    LogCreate,
    LogResponse,
)

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("", response_model=LogResponse, status_code=201)
def create_log(body: LogCreate, session: Session = Depends(get_session)):
    """Create a new emission log entry with auto-calculated CO₂e."""

    # Validate category
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category '{body.category}'. Must be one of: {sorted(VALID_CATEGORIES)}",
        )

    # Validate sub_type belongs to category
    if body.sub_type not in EMISSION_FACTORS.get(body.category, {}):
        valid_subs = sorted(EMISSION_FACTORS[body.category].keys())
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sub_type '{body.sub_type}' for category '{body.category}'. Must be one of: {valid_subs}",
        )

    # Look up emission factor and calculate CO₂e
    factor = EMISSION_FACTORS[body.category][body.sub_type]
    co2e_kg = round(body.quantity * factor, 4)
    unit = CATEGORY_UNITS[body.category]

    # Handle special unit for streaming (hours, not items)
    if body.sub_type == "streaming_hr":
        unit = "hr"

    log = EmissionLog(
        category=body.category,
        sub_type=body.sub_type,
        quantity=body.quantity,
        unit=unit,
        co2e_kg=co2e_kg,
        note=body.note,
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


@router.get("", response_model=list[LogResponse])
def list_logs(
    days: Optional[int] = Query(default=7, ge=1, le=365),
    session: Session = Depends(get_session),
):
    """Get emission logs from the last N days, ordered newest-first."""

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    statement = (
        select(EmissionLog)
        .where(EmissionLog.logged_at >= cutoff)
        .order_by(EmissionLog.logged_at.desc())  # type: ignore[union-attr]
    )
    results = session.exec(statement).all()
    return results


@router.get("/summary")
def logs_summary(
    days: Optional[int] = Query(default=7, ge=1, le=365),
    session: Session = Depends(get_session),
):
    """Get aggregated CO₂e summary by category for the last N days."""

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    statement = (
        select(EmissionLog)
        .where(EmissionLog.logged_at >= cutoff)
    )
    logs = session.exec(statement).all()

    totals: dict[str, float] = {}
    for log in logs:
        totals[log.category] = totals.get(log.category, 0) + log.co2e_kg

    grand_total = sum(totals.values())

    return {
        "days": days,
        "total_co2e_kg": round(grand_total, 2),
        "by_category": {k: round(v, 2) for k, v in sorted(totals.items())},
        "entry_count": len(logs),
    }


@router.delete("/{log_id}", status_code=204)
def delete_log(log_id: int, session: Session = Depends(get_session)):
    """Delete a log entry by ID."""

    log = session.get(EmissionLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    session.delete(log)
    session.commit()
