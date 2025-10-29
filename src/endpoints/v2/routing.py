import json

import httpx
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse
from redis import Redis

from src.core.config import settings
from src.core.worker import run_catchment_area
from src.schemas.ab_routing import IMotisPlan, motis_plan_examples
from src.schemas.catchment_area import (
    ICatchmentAreaActiveMobility,
    ICatchmentAreaCar,
    request_examples,
)
from src.schemas.one_to_all import OneToAllRequest, motis_onetoall_examples
from src.schemas.one_to_many import OneToManyRequest, motis_onetomany_examples
from src.schemas.status import ProcessingStatus

router = APIRouter()
redis = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
)


@router.post(
    "/active-mobility/catchment-area",
    summary="Compute catchment areas for active mobility",
)
async def compute_active_mobility_catchment_area(
    *,
    params: ICatchmentAreaActiveMobility = Body(
        ...,
        examples=request_examples["catchment_area_active_mobility"],
        description="The catchment area parameters.",
    ),
):
    """Compute catchment areas for active mobility."""

    return await compute_catchment_area(params)


@router.post(
    "/motorized-mobility/catchment-area",
    summary="Compute catchment areas for motorized mobility",
)
async def compute_motorized_mobility_catchment_area(
    *,
    params: ICatchmentAreaCar = Body(
        ...,
        examples=request_examples["catchment_area_motorized_mobility"],
        description="The catchment area parameters.",
    ),
):
    """Compute catchment areas for motorized mobility."""

    return await compute_catchment_area(params)


async def compute_catchment_area(
    params: ICatchmentAreaActiveMobility | ICatchmentAreaCar,
):
    # Get processing status of catchment area request
    processing_status = redis.get(str(params.layer_id))
    processing_status = processing_status.decode("utf-8") if processing_status else None

    if processing_status is None:
        # Initiate catchment area computation for request
        redis.set(str(params.layer_id), ProcessingStatus.in_progress.value)
        params = json.loads(params.json()).copy()
        run_catchment_area.delay(params)
        return JSONResponse(
            content={
                "result": ProcessingStatus.in_progress.value,
                "message": "Catchment area computation in progress.",
            },
            status_code=202,
        )
    elif processing_status == ProcessingStatus.in_progress.value:
        # Catchment area computation is in progress
        return JSONResponse(
            content={
                "result": processing_status,
                "message": "Catchment area computation in progress.",
            },
            status_code=202,
        )
    elif processing_status == ProcessingStatus.success.value:
        # Catchment area computation was successful
        return JSONResponse(
            content={
                "result": processing_status,
                "message": "Catchment area computed successfully.",
            },
            status_code=201,
        )
    elif processing_status == ProcessingStatus.disconnected_origin.value:
        # Catchment area computation failed
        return JSONResponse(
            content={
                "result": processing_status,
                "message": "Starting point(s) are disconnected from the street network.",
            },
            status_code=400,
        )
    else:
        # Catchment area computation failed
        return JSONResponse(
            content={
                "result": processing_status,
                "message": "Failed to compute catchment area.",
            },
            status_code=500,
        )


# --------------------- AB-Routing Endpoint -------------------- #


@router.post(
    "/ab-routing",
    summary="Compute AB-routing using motis",
)
async def compute_ab_routing(
    params: IMotisPlan = Body(
        ...,
        example=motis_plan_examples["default"],
        description="The motis plan service required parameters.",
    ),
):
    """
    Compute a routing plan by forwarding a request to the motis service.
    """
    return await compute_motis_request(params)


async def compute_motis_request(params: IMotisPlan):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                settings.MOTIS_PLAN_ENDPOINT, params=params.dict(by_alias=True)
            )
            response.raise_for_status()

            return JSONResponse(
                {"result": response.json(), "status_code": response.status_code}
            )

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from motis service: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"Cannot connect to motis service: {e}"
            )


# -------------------- One-to-All Routing Endpoint -------------------- #


@router.post(
    "/one-to-all",
    summary="Calculate Reachable Stations",
)
async def calculate_one_to_all(
    params: OneToAllRequest = Body(
        ...,
        example=motis_onetoall_examples["reachability_from_coordinate_with_time"],
        description="This endpoint calculates reachable stations within a specified duration from a starting location.",
    ),
):
    return await compute_one_to_all_request(params)


async def compute_one_to_all_request(params: OneToAllRequest):
    async with httpx.AsyncClient() as client:
        try:
            payload = params.dict(by_alias=True)
            response: httpx.Response = await client.get(
                settings.MOTIS_ONETOALL_ENDPOINT, params=payload
            )
            response.raise_for_status()
            return JSONResponse(
                {"result": response.json(), "status_code": response.status_code}
            )

        except httpx.HTTPStatusError as e:
            # This handles errors from a successful connection (e.g., 400, 404, 500)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from motis service: {e.response.text}",
            )

        except httpx.RequestError as e:
            # This handles network errors (e.g., connection refused, DNS lookup failed)
            raise HTTPException(
                status_code=503,  # 503 Service Unavailable is the correct code
                detail=f"Cannot connect to motis service: {e}",
            )


# -------------------- One-to-Many Routing Endpoint -------------------- #


async def compute_one_to_many_request(params: OneToManyRequest):
    """
    Sends the request to the external routing service and handles responses.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Convert Pydantic model to a dictionary using aliases (e.g., max_travel_time -> max)
            # `exclude_none=True` is good practice to avoid sending optional fields that are not set.
            payload = params.dict(by_alias=True, exclude_none=True)

            # Make the GET request to the external service with the payload as query parameters
            response: httpx.Response = await client.get(
                settings.MOTIS_ONETOMANY_ENDPOINT, params=payload
            )

            # Raise an exception for 4xx or 5xx status codes
            response.raise_for_status()

            # This pattern returns a JSON object containing the result from the upstream
            # service and its status code. FastAPI will wrap this in a 200 OK response.
            return JSONResponse(
                content={"result": response.json(), "status_code": response.status_code}
            )

        except httpx.HTTPStatusError as e:
            # Handle non-2xx responses from the external service (e.g., 400 Bad Request, 500 Server Error)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from routing service: {e.response.text}",
            )

        except httpx.RequestError as e:
            # Handle network-level errors (e.g., connection failed, DNS error)
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail=f"Cannot connect to the routing service: {str(e)}",
            )


@router.post(
    "/one-to-many",
    summary="Calculate One-to-Many Routes",
    # You can also add a response_model for better documentation
)
async def calculate_one_to_many(
    params: OneToManyRequest = Body(
        ...,
        # Use a relevant example for better API documentation (e.g., Swagger UI)
        example=motis_onetomany_examples["bike_tour_berlin"]["payload"],
        description="Calculates travel time and routes from a single origin to "
        "multiple destinations based on the provided parameters.",
    ),
):
    """
    This endpoint serves as a proxy to an external routing service,
    calculating travel times from one point to many destinations.
    """
    return await compute_one_to_many_request(params)
