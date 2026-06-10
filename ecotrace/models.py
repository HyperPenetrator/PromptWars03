"""
Data models for EcoTrace.

- EmissionLog: one entry per user-reported emission event.
- Goal: a monthly CO₂e reduction target per category.
- EMISSION_FACTORS: built-in lookup table (kg CO₂e per unit).
"""

from datetime import date, datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Field, SQLModel

# ---------------------------------------------------------------------------
# Emission Factor Lookup Table (global averages — no API needed)
# ---------------------------------------------------------------------------

EMISSION_FACTORS: dict[str, dict[str, float]] = {
    "transport": {
        "car_petrol": 0.171,       # kg CO₂e per km
        "car_electric": 0.053,
        "bus": 0.089,
        "train": 0.041,
        "flight_short": 0.255,     # per km
        "flight_long": 0.195,
        "cycling": 0.000,
    },
    "energy": {
        "electricity_grid": 0.233,  # kg CO₂e per kWh (global avg)
        "natural_gas": 0.202,
        "heating_oil": 0.298,
    },
    "diet": {
        "beef_meal": 3.000,         # kg CO₂e per meal
        "pork_meal": 1.200,
        "chicken_meal": 0.690,
        "fish_meal": 0.600,
        "vegetarian_meal": 0.320,
        "vegan_meal": 0.160,
    },
    "shopping": {
        "clothing_item": 10.000,    # kg CO₂e per item (avg fast fashion)
        "electronics_item": 80.000,
        "streaming_hr": 0.036,
    },
}

# Flat set of valid categories and sub_types for validation
VALID_CATEGORIES = set(EMISSION_FACTORS.keys())
VALID_SUB_TYPES = {
    sub: cat
    for cat, subs in EMISSION_FACTORS.items()
    for sub in subs
}

# Units expected per category
CATEGORY_UNITS: dict[str, str] = {
    "transport": "km",
    "energy": "kWh",
    "diet": "meal",
    "shopping": "item",
}


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------

class EmissionLog(SQLModel, table=True):
    """A single emission event logged by the user."""

    id: Optional[int] = Field(default=None, primary_key=True)
    category: str = Field(index=True)          # "transport" | "energy" | "diet" | "shopping"
    sub_type: str          # e.g. "car_petrol", "flight_short", "beef_meal"
    quantity: float        # km driven, kWh used, meals eaten, items bought
    unit: str              # "km" | "kWh" | "meal" | "item"
    co2e_kg: float         # Pre-calculated CO₂ equivalent in kg
    logged_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )
    note: Optional[str] = None


class Goal(SQLModel, table=True):
    """A monthly CO₂e reduction target for a category."""

    id: Optional[int] = Field(default=None, primary_key=True)
    category: str = Field(index=True)
    target_co2e_kg: float          # Monthly reduction target
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deadline: date


# ---------------------------------------------------------------------------
# Pydantic Request / Response Schemas
# ---------------------------------------------------------------------------

class LogCreate(BaseModel):
    """Request body for creating an emission log."""

    category: str
    sub_type: str
    quantity: float = PydanticField(gt=0, description="Must be positive")
    note: Optional[str] = None


class LogResponse(BaseModel):
    """Response body for a single emission log entry."""

    id: int
    category: str
    sub_type: str
    quantity: float
    unit: str
    co2e_kg: float
    logged_at: datetime
    note: Optional[str]


class GoalCreate(BaseModel):
    """Request body for creating a goal."""

    category: str
    target_co2e_kg: float = PydanticField(gt=0)
    deadline: date


class GoalUpdate(BaseModel):
    """Request body for updating a goal."""

    target_co2e_kg: Optional[float] = PydanticField(default=None, gt=0)
    deadline: Optional[date] = None


class GoalResponse(BaseModel):
    """Response body for a goal with progress."""

    id: int
    category: str
    target_co2e_kg: float
    current_co2e_kg: float
    progress_pct: float
    created_at: datetime
    deadline: date
