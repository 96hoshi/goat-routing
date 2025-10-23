# tests/utils/models.py
from dataclasses import dataclass
from typing import Any, Dict, List, NamedTuple, Optional


@dataclass
class QueryResult:
    """Standardized result structure for all routing services."""

    success: bool
    data: Optional[Dict[str, Any]]
    response_size: int  # in bytes
    error_message: Optional[str] = None
    status_code: Optional[int] = None

    @classmethod
    def success_result(
        cls, data: Dict[str, Any], response_size: int, status_code: int = 200
    ):
        return cls(
            success=True,
            data=data,
            response_size=response_size,
            status_code=status_code,
        )

    @classmethod
    def error_result(cls, error_message: str):
        return cls(
            success=False,
            data=None,
            response_size=0,
            error_message=error_message,
            status_code=None,
        )


# A new result class to hold all metrics
class BenchmarkResult(NamedTuple):
    latency_ms: float
    response_size_bytes: int
    status_code: int
    container_name: str
    container_cpu_usage_total_s: float  # Total CPU seconds used by container
    container_mem_peak_mb: float  # Peak memory usage of container
    container_net_rx_bytes: int  # Network Received
    container_net_tx_bytes: int  # Network Transmitted
    response_data: Dict | str


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

    def is_empty(self) -> bool:
        return (
            self.duration_s == 0
            and self.distance_m == 0.0
            and self.num_routes == 0
            and len(self.modes) == 0
            and len(self.vehicle_lines) == 0
        )
