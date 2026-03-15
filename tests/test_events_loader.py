from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llm_observability_analytics.contracts.models import (
    LatencyRecord,
    LLMInteractionEvent,
    ModelExecutionContext,
    RetrievalTraceEvent,
    SourceGroundingReference,
    TokenUsageRecord,
)
from llm_observability_analytics.events.loader import (
    load_interaction_events,
    load_retrieval_trace_events,
)


def _ts(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 1, 1, hour, minute, 0, tzinfo=UTC)


def _grounding_ref() -> SourceGroundingReference:
    return SourceGroundingReference(
        query_id="qry-1",
        trace_id="trc-1",
        document_id="doc-1",
        chunk_id="chk-1",
        source_id="src-1",
        dataset_version="ds-v1",
        rank=0,
        score=0.99,
    )


def _context() -> ModelExecutionContext:
    return ModelExecutionContext(
        query_id="qry-1",
        trace_id="trc-1",
        model_version="gpt-5.4",
        dataset_version="ds-v1",
        provider="openai",
        model_name="gpt-5.4-mini",
    )


def _token_usage() -> TokenUsageRecord:
    return TokenUsageRecord(
        query_id="qry-1",
        trace_id="trc-1",
        model_version="gpt-5.4",
        dataset_version="ds-v1",
        input_tokens=120,
        output_tokens=45,
        recorded_at=_ts(10, 1),
    )


def _latency() -> LatencyRecord:
    return LatencyRecord(
        query_id="qry-1",
        trace_id="trc-1",
        request_timestamp=_ts(10, 0),
        response_timestamp=_ts(10, 0),
        latency_ms=342,
        stage="end_to_end",
    )


def _interaction_payload() -> dict[str, object]:
    return LLMInteractionEvent(
        query_id="qry-1",
        trace_id="trc-1",
        request_timestamp=_ts(10, 0),
        response_timestamp=_ts(10, 0),
        prompt_text="Summarize incident",
        response_text="Root cause was cert expiration.",
        model_context=_context(),
        token_usage=_token_usage(),
        latency=_latency(),
        retrieval_references=[_grounding_ref()],
    ).to_dict()


def _retrieval_payload() -> dict[str, object]:
    return RetrievalTraceEvent(
        query_id="qry-1",
        trace_id="trc-1",
        retrieval_timestamp=_ts(10, 0),
        query_text="how to deploy service",
        retrieval_system="hybrid-search",
        top_k=5,
        references=[_grounding_ref()],
        model_version="gpt-5.4",
        dataset_version="ds-v1",
    ).to_dict()


def _write_jsonl(path: Path, payloads: list[dict[str, object]]) -> None:
    lines = "\n".join(json.dumps(p) for p in payloads) + "\n"
    path.write_text(lines, encoding="utf-8")


def test_load_interaction_events_success_and_max_events(tmp_path: Path) -> None:
    path = tmp_path / "interactions.jsonl"
    _write_jsonl(path, [_interaction_payload(), _interaction_payload()])

    events = load_interaction_events(path, max_events=1)
    assert len(events) == 1
    assert events[0].query_id == "qry-1"


def test_load_retrieval_trace_events_success(tmp_path: Path) -> None:
    path = tmp_path / "retrievals.jsonl"
    _write_jsonl(path, [_retrieval_payload()])

    events = load_retrieval_trace_events(path, max_events=100)
    assert len(events) == 1
    assert events[0].retrieval_system == "hybrid-search"


def test_loader_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Input file does not exist"):
        load_interaction_events(tmp_path / "missing.jsonl", max_events=10)


def test_loader_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text("{not valid json}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON"):
        load_interaction_events(path, max_events=10)


def test_loader_rejects_non_object_json_line(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text("[]\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected object JSON"):
        load_retrieval_trace_events(path, max_events=10)


def test_loader_wraps_contract_validation_errors(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text('{"query_id":"only-one-field"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid interaction event"):
        load_interaction_events(path, max_events=10)
