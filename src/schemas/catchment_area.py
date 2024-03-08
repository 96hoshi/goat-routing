from enum import Enum
from typing import List
from uuid import UUID

import polars as pl
from pydantic import BaseModel, Field, validator

SEGMENT_DATA_SCHEMA = {
    "id": pl.Int64,
    "length_m": pl.Float64,
    "length_3857": pl.Float64,
    "class_": pl.Utf8,
    "impedance_slope": pl.Float64,
    "impedance_slope_reverse": pl.Float64,
    "impedance_surface": pl.Float32,
    "coordinates_3857": pl.Utf8,
    "source": pl.Int64,
    "target": pl.Int64,
    "tags": pl.Utf8,
    "h3_3": pl.Int32,
    "h3_6": pl.Int32,
}

VALID_WALKING_CLASSES = [
    "secondary",
    "tertiary",
    "residential",
    "livingStreet",
    "trunk",
    "unclassified",
    "parkingAisle",
    "driveway",
    "pedestrian",
    "footway",
    "steps",
    "track",
    "bridleway",
    "unknown",
]

VALID_BICYCLE_CLASSES = [
    "secondary",
    "tertiary",
    "residential",
    "livingStreet",
    "trunk",
    "unclassified",
    "parkingAisle",
    "driveway",
    "pedestrian",
    "track",
    "cycleway",
    "bridleway",
    "unknown",
]


class CatchmentAreaType(str, Enum):
    """Catchment area type schema."""

    polygon = "polygon"
    network = "network"
    rectangular_grid = "rectangular_grid"


class CatchmentAreaStartingPoints(BaseModel):
    """Base model for catchment area attributes."""

    latitude: List[float] | None = Field(
        None,
        title="Latitude",
        description="The latitude of the catchment area center.",
    )
    longitude: List[float] | None = Field(
        None,
        title="Longitude",
        description="The longitude of the catchment area center.",
    )


class RoutingActiveMobilityType(str, Enum):
    """Routing active mobility type schema."""

    walking = "walking"
    bicycle = "bicycle"
    pedelec = "pedelec"


class TravelTimeCostActiveMobility(BaseModel):
    """Travel time cost schema."""

    max_traveltime: int = Field(
        ...,
        title="Max Travel Time",
        description="The maximum travel time in minutes.",
        ge=1,
        le=45,
    )
    steps: int = Field(
        ...,
        title="Steps",
        description="The number of steps.",
    )
    speed: int = Field(
        ...,
        title="Speed",
        description="The speed in km/h.",
        ge=1,
        le=25,
    )

    # Ensure the number of steps doesn't exceed the maximum traveltime
    @validator("steps", pre=True, always=True)
    def valid_num_steps(cls, v):
        if v > 45:
            raise ValueError(
                "The number of steps must not exceed the maximum traveltime."
            )
        return v


# TODO: Check how to treat miles
class TravelDistanceCostActiveMobility(BaseModel):
    """Travel distance cost schema."""

    max_distance: int = Field(
        ...,
        title="Max Distance",
        description="The maximum distance in meters.",
        ge=50,
        le=20000,
    )
    steps: int = Field(
        ...,
        title="Steps",
        description="The number of steps.",
    )

    # Ensure the number of steps doesn't exceed the maximum distance
    @validator("steps", pre=True, always=True)
    def valid_num_steps(cls, v):
        if v > 20000:
            raise ValueError(
                "The number of steps must not exceed the maximum distance."
            )
        return v


class ICatchmentAreaActiveMobility(BaseModel):
    """Model for the active mobility catchment area request."""

    starting_points: CatchmentAreaStartingPoints = Field(
        ...,
        title="Starting Points",
        description="The starting points of the catchment area.",
    )
    routing_type: RoutingActiveMobilityType = Field(
        ...,
        title="Routing Type",
        description="The routing type of the catchment area.",
    )
    travel_cost: TravelTimeCostActiveMobility | TravelDistanceCostActiveMobility = (
        Field(
            ...,
            title="Travel Cost",
            description="The travel cost of the catchment area.",
        )
    )
    scenario_id: UUID | None = Field(
        None,
        title="Scenario ID",
        description="The ID of the scenario that is used for the routing.",
    )
    catchment_area_type: CatchmentAreaType = Field(
        ...,
        title="Return Type",
        description="The return type of the catchment area.",
    )
    polygon_difference: bool | None = Field(
        None,
        title="Polygon Difference",
        description="If true, the polygons returned will be the geometrical difference of two following calculations.",
    )
    result_table: str = Field(
        ...,
        title="Result Table",
        description="The table name the results should be saved.",
    )
    layer_id: UUID | None = Field(
        ...,
        title="Layer ID",
        description="The ID of the layer the results should be saved.",
    )

    # Check that polygon difference exists if catchment area type is polygon
    @validator("polygon_difference", pre=True, always=True)
    def check_polygon_difference(cls, v, values):
        if (
            values["catchment_area_type"] == CatchmentAreaType.polygon.value
            and v is None
        ):
            raise ValueError(
                "The polygon difference must be set if the catchment area type is polygon."
            )
        return v

    # Check that polygon difference is not specified if catchment area type is not polygon
    @validator("polygon_difference", pre=True, always=True)
    def check_polygon_difference_not_specified(cls, v, values):
        if (
            values["catchment_area_type"] != CatchmentAreaType.polygon.value
            and v is not None
        ):
            raise ValueError(
                "The polygon difference must not be set if the catchment area type is not polygon."
            )
        return v


request_examples = {
    "catchment_area_active_mobility": {
        # 1. Single catchment area for walking (time based)
        "single_point_walking_time": {
            "summary": "Single point catchment area walking (time based)",
            "value": {
                "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
                "routing_type": "walking",
                "travel_cost": {
                    "max_traveltime": 30,
                    "steps": 5,
                    "speed": 5,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 2. Single catchment area for walking (distance based)
        "single_point_walking_distance": {
            "summary": "Single point catchment area walking (distance based)",
            "value": {
                "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
                "routing_type": "walking",
                "travel_cost": {
                    "max_distance": 2500,
                    "steps": 100,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 3. Single catchment area for cycling
        "single_point_cycling": {
            "summary": "Single point catchment area cycling",
            "value": {
                "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
                "routing_type": "bicycle",
                "travel_cost": {
                    "max_traveltime": 15,
                    "steps": 5,
                    "speed": 15,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 4. Single catchment area for walking with scenario
        "single_point_walking_scenario": {
            "summary": "Single point catchment area walking",
            "value": {
                "starting_points": {"latitude": [52.5200], "longitude": [13.4050]},
                "routing_type": "walking",
                "travel_cost": {
                    "max_traveltime": 30,
                    "steps": 10,
                    "speed": 5,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "scenario_id": "e7dcaae4-1750-49b7-89a5-9510bf2761ad",
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 5. Multi-catchment area walking with more than one starting point
        "multi_point_walking": {
            "summary": "Multi point catchment area walking",
            "value": {
                "starting_points": {
                    "latitude": [
                        52.5200,
                        52.5210,
                        52.5220,
                        52.5230,
                        52.5240,
                        52.5250,
                        52.5260,
                        52.5270,
                        52.5280,
                        52.5290,
                    ],
                    "longitude": [
                        13.4050,
                        13.4060,
                        13.4070,
                        13.4080,
                        13.4090,
                        13.4100,
                        13.4110,
                        13.4120,
                        13.4130,
                        13.4140,
                    ],
                },
                "routing_type": "walking",
                "travel_cost": {
                    "max_traveltime": 30,
                    "steps": 10,
                    "speed": 5,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
        # 6. Multi-catchment area cycling with more than one starting point
        "multi_point_cycling": {
            "summary": "Multi point catchment area cycling",
            "value": {
                "starting_points": {
                    "latitude": [
                        52.5200,
                        52.5210,
                        52.5220,
                        52.5230,
                        52.5240,
                        52.5250,
                        52.5260,
                        52.5270,
                        52.5280,
                        52.5290,
                    ],
                    "longitude": [
                        13.4050,
                        13.4060,
                        13.4070,
                        13.4080,
                        13.4090,
                        13.4100,
                        13.4110,
                        13.4120,
                        13.4130,
                        13.4140,
                    ],
                },
                "routing_type": "bicycle",
                "travel_cost": {
                    "max_traveltime": 15,
                    "steps": 5,
                    "speed": 15,
                },
                "catchment_area_type": "polygon",
                "polygon_difference": True,
                "result_table": "polygon_744e4fd1685c495c8b02efebce875359",
                "layer_id": "744e4fd1-685c-495c-8b02-efebce875359",
            },
        },
    }
}
