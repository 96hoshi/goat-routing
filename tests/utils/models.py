# tests/utils/models.py
from dataclasses import dataclass


@dataclass
class ServiceMetrics:
    """Holds the performance metrics for a single API call."""

    time_ms: float
    cpu_s: float
    mem_mb_delta: float
    response_size_bytes: int
    status_code: int
    response_data: dict | str  # To hold the JSON response for later writing
