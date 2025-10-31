from datetime import datetime
from textwrap import dedent
from typing import Any, Dict, List, Optional

from src.core.config import settings
from tests.conftest import TIME_BENCH


# ----------- PAYLOAD BUILDERS ----------- #
def motis_payload(
    origin: str,
    destination: str,
    time: str = TIME_BENCH,
    detailed_transfers: bool = False,
    maxItineraries: Optional[int] = None,
    **kwargs,
) -> Dict[str, str]:
    """
    Build a payload for the Motis routing API.
    """
    detailed: str = "true" if detailed_transfers else "false"

    payload = {
        "fromPlace": origin,
        "toPlace": destination,
        "time": time,
        "detailedTransfers": detailed,
        "numItineraries": maxItineraries,
        "maxItineraries": maxItineraries,
        **kwargs,
    }
    return {k: v for k, v in payload.items() if v is not None}


def one_to_all_payload(
    start_location: str,
    max_travel_time: int,
    time: Optional[str] = None,
    transit_modes: Optional[List[str]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Builds a request payload for the MOTIS "one-to-all" service.
    """
    payload = {
        "one": start_location,
        "maxTravelTime": max_travel_time,
        "time": time,
        "transitModes": transit_modes,
        **kwargs,
    }

    # Cleanly remove any optional keys that were not provided (i.e., are None)
    return {k: v for k, v in payload.items() if v is not None}


def google_payload(
    origin: str,
    destination: str,
    mode: str = "transit",
    time: str = TIME_BENCH,
    api_key: str = settings.GOOGLE_API_KEY,
    alternatives: bool = True,
) -> Dict[str, Any]:
    """Build payload for Google Directions API."""

    dt = datetime.fromisoformat(time.replace("Z", "+00:00"))
    departure_timestamp = int(dt.timestamp())
    alternatives_str = "true" if alternatives else "false"

    return {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "departure_time": departure_timestamp,
        "key": api_key,
        "alternatives": alternatives_str,  # default is 1
    }


def valhalla_payload(
    origin: str, destination: str, costing: str = "multimodal", **kwargs
) -> Dict[str, Any]:
    """Build payload for Valhalla routing API.
    costing values: "multimodal", "auto", "bicycle", "pedestrian", "bus"
    """

    origin_lat, origin_lon = map(float, origin.split(","))
    dest_lat, dest_lon = map(float, destination.split(","))

    return {
        "locations": [
            {"lat": origin_lat, "lon": origin_lon},
            {"lat": dest_lat, "lon": dest_lon},
        ],
        "costing": costing,
        "directions_options": {"units": "kilometers"},
        **kwargs,
    }


def otp_payload(
    origin: str,
    destination: str,
    transport_modes: list[str] = ["TRANSIT", "WALK"],
    time: str = TIME_BENCH.split("T")[1].replace("Z", ""),
    date: str = TIME_BENCH.split("T")[0],
) -> dict[str, Any]:
    """Build minimal GraphQL payload for OTP CAR test."""

    def parse_coords(coord_str: str) -> dict[str, float]:
        lat, lon = map(float, coord_str.split(","))
        return {"lat": lat, "lon": lon}

    query = dedent(
        """
        query PlanTrip(
          $from: InputCoordinates!,
          $to: InputCoordinates!,
          $date: String!,
          $time: String!,
          $transportModes: [TransportMode!]!
        ) {
          plan(
            from: $from,
            to: $to,
            date: $date,
            time: $time,
            transportModes: $transportModes
          ) {
            date
            from { name lat lon }
            to { name lat lon }
            itineraries {
              startTime
              endTime
              duration
              legs {
                startTime
                endTime
                mode
                duration
                distance
                from { name lat lon }
                to { name lat lon }
                route {
                  shortName
                  longName
                }
              }
            }
          }
        }
        """
    )

    variables = {
        "from": parse_coords(origin),
        "to": parse_coords(destination),
        "transportModes": [{"mode": mode} for mode in transport_modes],
        "date": date,
        "time": time,
    }

    return {"query": query.strip(), "variables": variables}
