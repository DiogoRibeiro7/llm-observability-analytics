from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MetricRecord:
    metric_name: str
    metric_value: float
    dimension_key: str
    dimension_value: str


@dataclass(frozen=True, slots=True)
class AnalyticsSummary:
    request_count: int
    retrieval_trace_count: int
    latency_mean_ms: float
    latency_p50_ms: float
    latency_p95_ms: float
    total_tokens: int
    average_tokens_per_request: float
    retrieval_hit_count: int
    grounded_response_count: int
    ungrounded_response_count: int
    feedback_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)
