from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TraceReference:
    trace_id: str
    query_id: str
