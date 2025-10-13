# tests/utils/models.py
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class QueryResult:
    """Standardized result structure for all routing services."""

    success: bool
    data: Optional[Dict[str, Any]]
    response_size: int
    error_message: Optional[str] = None

    @classmethod
    def success_result(cls, data: Dict[str, Any], response_size: int):
        return cls(success=True, data=data, response_size=response_size)

    @classmethod
    def error_result(cls, error_message: str):
        return cls(
            success=False, data=None, response_size=0, error_message=error_message
        )


@dataclass
class ServiceMetrics:
    """Holds the performance metrics for a single API call."""

    time_ms: float
    cpu_s: float
    mem_mb_delta: float
    response_size_bytes: int
    status_code: int
    response_data: dict | str


@dataclass
class RouteSummary:
    """Summarizes key aspects of a routing response."""

    duration_s: int
    distance_m: float
    num_routes: int
    modes: List[str]
    vehicle_lines: List[str]

    @staticmethod
    def empty_summary():
        return RouteSummary(
            duration_s=0,
            distance_m=0.0,
            num_routes=0,
            modes=[],
            vehicle_lines=[],
        )
