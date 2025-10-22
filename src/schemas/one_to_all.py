from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.schemas.ab_routing import MotisMode


class ElevationCosts(str, Enum):
    """Enum for elevation cost profiles."""

    NONE = "NONE"
    LOW = "LOW"
    HIGH = "HIGH"

class OneToAllRequest(BaseModel):
    """
    Pydantic model for a MOTIS 'one-to-all' (reachability) request.
    """

    start_location: str = Field(
        ...,
        alias="one",
        title="Start Location",
        description="The starting point as a station ID or 'latitude,longitude' string.",
        examples=["8000261", "52.520008,13.404954"],  # Munich Hbf, Berlin Mitte
    )
    start_time: Optional[str] = Field(
        alias="time",
        title="Start Time",
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        description="Start time for the search in ISO 8601 format. Defaults to the current time.",
    )
    duration_limit: int = Field(
        ...,
        alias="maxTravelTime",
        title="Duration Limit (seconds)",
        description="The maximum travel duration in seconds to search for.",
        gt=0,  # Duration must be greater than 0
        examples=[3600],
    )
    transit_modes: Optional[List[MotisMode]] = Field(
        default_factory=lambda: [MotisMode.WALK, MotisMode.TRANSIT],
        alias="transitModes",
        title="Transit Modes",
        description="A list of transit modes to be used in the search.",
    )

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


motis_onetoall_examples = {
    "default": {
        "one": "50.7754385,6.0815102",  
        "maxTravelTime": 90
    },
    "reachability_from_station": {
        "one": "8011160",  # Berlin Hbf
        "maxTravelTime": 90,
        "transitModes": [MotisMode.WALK.value, MotisMode.TRANSIT.value]
},
    "reachability_from_coordinate_with_time": {
        "one": "50.7754385,6.0815102",  
        "maxTravelTime": 90,
        "time": "2025-09-15T10:00:00Z",
        "transitModes": [MotisMode.WALK.value, MotisMode.TRANSIT.value]
    },
    "reachability_walk_only": {
        "one": "8000261",  # Munich Hbf
        "maxTravelTime": 90,
        "transitModes": [MotisMode.WALK.value]
    },
}
