from typing import List

from pydantic import BaseModel, Field

from src.schemas.ab_routing import MotisMode


class OneToManyRequest(BaseModel):

    """
    A Pydantic model representing the parameters for a routing request.
    """

    one: str = Field(..., description="A single geo location as latitude;longitude.")

    many: List[str] = Field(
        ..., description="A list of geo locations, each as latitude;longitude."
    )

    # Note: `max` is a built-in function, so we use an alias.
    max: int = Field(
        ..., alias="max", description="Maximum travel time in seconds.", gt=0
    )

    maxMatchingDistance: int = Field(
        ...,
        alias="maxMatchingDistance",
        description="Maximum matching distance in meters to match geo coordinates to the street network.",
        gt=0,
    )

    mode: MotisMode = Field(
        description="Routing profile to use (currently supported: WALK, BIKE, CAR).",
    )

    arriveBy: bool = Field(
        ...,
        alias="arriveBy",
        description="If True, calculates many-to-one routes. If False, calculates one-to-many routes.",
    )

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True


# --- Example Payloads ---

motis_onetomany_examples = {
    "walk_in_berlin": {
        "description": "A short walk from the Brandenburg Gate to the Reichstag Building.",
        "payload": {
            "one": "52.5163;13.3777",
            "many": ["52.5186;13.3762"],
            "mode": MotisMode.WALK.value,
            "max": 300,
            "maxMatchingDistance": 50,
            "arriveBy": False,
        },
    },
    "bike_tour_berlin": {
        "description": "A bike ride from the Brandenburg Gate to Potsdamer Platz and the TV Tower.",
        "payload": {
            "one": "52.5163;13.3777",
            "many": ["52.5096;13.3737", "52.5208;13.4094"],
            "mode": MotisMode.BIKE.value,
            "max": 900,
            "maxMatchingDistance": 50,
            "arriveBy": False,
        },
    },
    "car_trip_across_berlin": {
        "description": "A car trip from the Brandenburg Gate to the East Side Gallery.",
        "payload": {
            "one": "52.5163;13.3777",
            "many": ["52.5053;13.4429"],
            "mode": MotisMode.CAR.value,
            "max": 1200,
            "maxMatchingDistance": 50,
            "arriveBy": False,
        },
    },
}
