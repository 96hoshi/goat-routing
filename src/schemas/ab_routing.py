from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MotisMode(str, Enum):
    WALK = "WALK"
    BIKE = "BIKE"
    RENTAL = "RENTAL"
    CAR = "CAR"
    CAR_PARKING = "CAR_PARKING"
    CAR_DROPOFF = "CAR_DROPOFF"
    ODM = "ODM"
    FLEX = "FLEX"
    TRANSIT = "TRANSIT"
    TRAM = "TRAM"
    SUBWAY = "SUBWAY"
    FERRY = "FERRY"
    AIRPLANE = "AIRPLANE"
    METRO = "METRO"
    BUS = "BUS"
    COACH = "COACH"
    RAIL = "RAIL"
    HIGHSPEED_RAIL = "HIGHSPEED_RAIL"
    LONG_DISTANCE = "LONG_DISTANCE"
    NIGHT_RAIL = "NIGHT_RAIL"
    REGIONAL_FAST_RAIL = "REGIONAL_FAST_RAIL"
    REGIONAL_RAIL = "REGIONAL_RAIL"
    CABLE_CAR = "CABLE_CAR"
    FUNICULAR = "FUNICULAR"
    AREAL_LIFT = "AREAL_LIFT"
    OTHER = "OTHER"


class MotisPlace(BaseModel):
    name: str = Field(
        ...,
        title="Name",
        description="The name of the transit stop / PoI / address.",
    )
    lat: float = Field(
        ...,
        title="Latitude",
        description="The latitude of the place.",
    )
    lon: float = Field(
        ...,
        title="Longitude",
        description="The longitude of the place.",
    )
    level: float = Field(
        ...,
        title="Level",
        description="The level according to OpenStreetMap.",
    )


class IMotisPlan(BaseModel):
    """
    Model for the MOTIS plan service request, with corrected optional and
    mutually exclusive fields.
    """

    from_place: str = Field(
        ...,
        alias="fromPlace",
        title="From Place",
        description="The starting place as a 'latitude,longitude[,level]' tuple OR stop ID.",
    )
    to_place: str = Field(
        ...,
        alias="toPlace",
        title="To Place",
        description="The destination as a 'latitude,longitude[,level]' tuple OR stop ID.",
    )
    detailed_transfers: bool = Field(
        default=True,
        alias="detailedTransfers",
        title="Detailed Transfers",
        description="If true, compute transfer polylines and step instructions.",
    )

    # --- Optional Parameters ---
    time: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        description="Departure or arrival time in ISO 8601 format. Defaults to now.",
    )
    arrive_by: Optional[bool] = Field(
        default=False,
        alias="arriveBy",
        title="Arrive By",
        description="If true, `time` refers to arrival; otherwise, it's departure.",
    )
    transit_modes: Optional[List[str]] = Field(
        default_factory=lambda: [MotisMode.TRANSIT.value],  # A list as default
        alias="transitModes",
        title="Modes",
        description="Array of desired modes of transport.",
    )

    # --- Timetable-Dependent Fields ---
    num_itineraries: Optional[int] = Field(
        default=5,
        alias="numItineraries",
        title="Minimum Itineraries",
        description="The minimum number of itineraries to compute. Only relevant if timetableView=true.",
        ge=1,  # A minimum of 1 makes logical sense
    )

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


motis_plan_examples = {
    "default": {
        "fromPlace": "50.7754385,6.0815102",
        "toPlace": "50.7753455,6.0838868",
        "detailedTransfers": "false",
    },
    "detailed_with_time": {
        "fromPlace": "50.7754385,6.0815102",
        "toPlace": "50.7753455,6.0838868",
        "detailedTransfers": "true",
        "time": "2025-08-28T08:00:00Z",
        "arriveBy": "true",
    },
    "bus_with_time": {
        "fromPlace": "50.7950,6.1260",
        "toPlace": "50.7651,6.0821",
        "detailedTransfers": "false",
        "time": "2025-08-28T08:00:00Z",
        "arriveBy": "false",
        "transitModes": [MotisMode.BUS.value],
    },
}
