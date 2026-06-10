"""
Insights router — Gemini-powered emission analysis.

- POST /insights         → Generate fresh insights from recent logs
- GET  /insights/weekly  → Get weekly summary with trend comparison
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import EmissionLog
from agent.prompt_builder import build_user_prompt, build_weekly_prompt
from agent.gemini_client import generate_insight

router = APIRouter(prefix="/insights", tags=["insights"])


@router.post("")
def create_insight(
    days: int = 7,
    session: Session = Depends(get_session),
):
    """Generate AI-powered insights from recent emission logs."""

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    statement = (
        select(EmissionLog)
        .where(EmissionLog.logged_at >= cutoff)
        .order_by(EmissionLog.logged_at.desc())  # type: ignore[union-attr]
    )
    logs = list(session.exec(statement).all())

    user_prompt = build_user_prompt(logs)

    try:
        insight = generate_insight(user_prompt)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {
        "period_days": days,
        "log_count": len(logs),
        "insight": insight,
    }


@router.get("/weekly")
def weekly_summary(session: Session = Depends(get_session)):
    """
    Weekly summary with comparison to previous week.
    This week = last 7 days; previous week = 8–14 days ago.
    """

    now = datetime.now(timezone.utc)

    # This week's logs
    this_cutoff = now - timedelta(days=7)
    this_logs = list(
        session.exec(
            select(EmissionLog)
            .where(EmissionLog.logged_at >= this_cutoff)
            .order_by(EmissionLog.logged_at.desc())  # type: ignore[union-attr]
        ).all()
    )

    # Previous week's logs (for comparison)
    prev_start = now - timedelta(days=14)
    prev_end = now - timedelta(days=7)
    prev_logs = list(
        session.exec(
            select(EmissionLog)
            .where(EmissionLog.logged_at >= prev_start)
            .where(EmissionLog.logged_at < prev_end)
        ).all()
    )

    prev_total = sum(log.co2e_kg for log in prev_logs) if prev_logs else None
    user_prompt = build_weekly_prompt(this_logs, prev_total)

    try:
        insight = generate_insight(user_prompt)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {
        "period": "weekly",
        "this_week_entries": len(this_logs),
        "this_week_co2e_kg": round(sum(l.co2e_kg for l in this_logs), 2),
        "prev_week_co2e_kg": round(prev_total, 2) if prev_total is not None else None,
        "insight": insight,
    }
