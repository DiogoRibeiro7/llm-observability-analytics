from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm_observability_analytics.contracts.models import LLMInteractionEvent, RetrievalTraceEvent


def _load_jsonl(path: Path, max_events: int) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"Input file does not exist: {path}")

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, raw in enumerate(handle, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{idx}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"Expected object JSON at {path}:{idx}")
            rows.append(payload)
            if len(rows) >= max_events:
                break
    return rows


def load_interaction_events(path: Path, max_events: int) -> list[LLMInteractionEvent]:
    events: list[LLMInteractionEvent] = []
    for idx, payload in enumerate(_load_jsonl(path, max_events), start=1):
        try:
            events.append(LLMInteractionEvent.from_dict(payload))
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid interaction event at {path}:{idx}") from exc
    return events


def load_retrieval_trace_events(path: Path, max_events: int) -> list[RetrievalTraceEvent]:
    events: list[RetrievalTraceEvent] = []
    for idx, payload in enumerate(_load_jsonl(path, max_events), start=1):
        try:
            events.append(RetrievalTraceEvent.from_dict(payload))
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid retrieval event at {path}:{idx}") from exc
    return events
