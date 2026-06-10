"""
Goals CRUD router.

- POST   /goals         → Create a reduction goal
- GET    /goals         → List active goals with progress
- PATCH  /goals/{id}    → Update a goal
- DELETE /goals/{id}    → Remove a goal
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import (
    VALID_CATEGORIES,
    EmissionLog,
    Goal,
    GoalCreate,
    GoalResponse,
    GoalUpdate,
)

router = APIRouter(prefix="/goals", tags=["goals"])


def _calculate_progress(goal: Goal, session: Session) -> GoalResponse:
    """Calculate how much CO₂e the user emitted in this goal's category since creation."""

    statement = (
        select(EmissionLog)
        .where(EmissionLog.category == goal.category)
        .where(EmissionLog.logged_at >= goal.created_at)
    )
    logs = session.exec(statement).all()
    current_co2e = sum(log.co2e_kg for log in logs)

    # Progress = how much of the target has been "used"
    # 100% means the user hit their target (bad); 0% means no emissions logged
    if goal.target_co2e_kg > 0:
        progress_pct = round(min((current_co2e / goal.target_co2e_kg) * 100, 100), 1)
    else:
        progress_pct = 100.0

    return GoalResponse(
        id=goal.id,  # type: ignore[arg-type]
        category=goal.category,
        target_co2e_kg=goal.target_co2e_kg,
        current_co2e_kg=round(current_co2e, 2),
        progress_pct=progress_pct,
        created_at=goal.created_at,
        deadline=goal.deadline,
    )


@router.post("", response_model=GoalResponse, status_code=201)
def create_goal(body: GoalCreate, session: Session = Depends(get_session)):
    """Create a new CO₂e reduction goal for a category."""

    if body.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category '{body.category}'. Must be one of: {sorted(VALID_CATEGORIES)}",
        )

    goal = Goal(
        category=body.category,
        target_co2e_kg=body.target_co2e_kg,
        deadline=body.deadline,
    )
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return _calculate_progress(goal, session)


@router.get("", response_model=list[GoalResponse])
def list_goals(session: Session = Depends(get_session)):
    """List all goals with their current progress."""

    goals = session.exec(select(Goal)).all()
    return [_calculate_progress(g, session) for g in goals]


@router.patch("/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: int, body: GoalUpdate, session: Session = Depends(get_session)):
    """Update a goal's target or deadline."""

    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if body.target_co2e_kg is not None:
        goal.target_co2e_kg = body.target_co2e_kg
    if body.deadline is not None:
        goal.deadline = body.deadline

    session.add(goal)
    session.commit()
    session.refresh(goal)
    return _calculate_progress(goal, session)


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: int, session: Session = Depends(get_session)):
    """Delete a goal."""

    goal = session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    session.delete(goal)
    session.commit()
