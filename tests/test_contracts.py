from __future__ import annotations

from datetime import UTC, datetime

import pytest

from llm_observability_analytics.contracts.models import (
    OBSERVABILITY_CONTRACT_VERSION,
    LatencyRecord,
    LLMInteractionEvent,
    ModelExecutionContext,
    RetrievalTraceEvent,
    SourceGroundingReference,
    TokenUsageRecord,
    UserFeedbackEvent,
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
        temperature=0.1,
        max_tokens=1024,
        system_metadata={"app": "chat"},
        model_metadata={"tier": "prod"},
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


def test_model_execution_context_round_trip() -> None:
    context = _context()
    restored = ModelExecutionContext.from_json(context.to_json())
    assert restored == context


def test_source_grounding_reference_validation() -> None:
    ref = _grounding_ref()
    assert ref.document_id == "doc-1"

    with pytest.raises(ValueError, match="document_id"):
        SourceGroundingReference(
            query_id="qry-1",
            trace_id="trc-1",
            document_id="",
            chunk_id="chk-1",
        )


def test_token_usage_total_tokens_computed_and_validated() -> None:
    usage = _token_usage()
    assert usage.total_tokens == 165

    with pytest.raises(ValueError, match="total_tokens"):
        TokenUsageRecord(
            query_id="qry-1",
            trace_id="trc-1",
            model_version="gpt-5.4",
            dataset_version="ds-v1",
            input_tokens=10,
            output_tokens=5,
            total_tokens=99,
            recorded_at=_ts(11),
        )


def test_latency_record_invalid_timestamps() -> None:
    with pytest.raises(ValueError, match="response_timestamp"):
        LatencyRecord(
            query_id="qry-1",
            trace_id="trc-1",
            request_timestamp=_ts(12, 5),
            response_timestamp=_ts(12, 4),
            latency_ms=10,
        )


def test_user_feedback_event_validation() -> None:
    feedback = UserFeedbackEvent(
        query_id="qry-1",
        trace_id="trc-1",
        feedback_timestamp=_ts(12, 0),
        rating=4,
        feedback_text="Helpful answer.",
        model_version="gpt-5.4",
        dataset_version="ds-v1",
    )
    assert feedback.rating == 4

    with pytest.raises(ValueError, match="At least one of rating"):
        UserFeedbackEvent(
            query_id="qry-1",
            trace_id="trc-1",
            feedback_timestamp=_ts(12, 0),
        )


def test_retrieval_trace_event_round_trip() -> None:
    trace = RetrievalTraceEvent(
        query_id="qry-1",
        trace_id="trc-1",
        retrieval_timestamp=_ts(10, 0),
        query_text="how to deploy service",
        retrieval_system="hybrid-search",
        top_k=5,
        references=[_grounding_ref()],
        model_version="gpt-5.4",
        dataset_version="ds-v1",
    )
    parsed = RetrievalTraceEvent.from_json(trace.to_json())
    assert parsed == trace


def test_interaction_event_valid_and_serializable() -> None:
    interaction = LLMInteractionEvent(
        query_id="qry-1",
        trace_id="trc-1",
        request_timestamp=_ts(10, 0),
        response_timestamp=_ts(10, 0),
        prompt_text="Summarize incident root cause",
        response_text="Root cause was an expired certificate.",
        model_context=_context(),
        token_usage=_token_usage(),
        latency=_latency(),
        retrieval_references=[_grounding_ref()],
        user_metadata={"user_id": "u-1"},
        session_metadata={"session_id": "s-1"},
        feedback=UserFeedbackEvent(
            query_id="qry-1",
            trace_id="trc-1",
            feedback_timestamp=_ts(10, 5),
            feedback_label="thumbs_up",
            model_version="gpt-5.4",
        ),
    )
    parsed = LLMInteractionEvent.from_json(interaction.to_json())
    assert parsed == interaction
    assert parsed.model_version == "gpt-5.4"
    assert parsed.dataset_version == "ds-v1"
    assert parsed.latency_ms == 342


def test_interaction_event_rejects_mismatched_nested_ids() -> None:
    bad_token_usage = TokenUsageRecord(
        query_id="qry-2",
        trace_id="trc-1",
        model_version="gpt-5.4",
        dataset_version="ds-v1",
        input_tokens=1,
        output_tokens=1,
        recorded_at=_ts(10, 1),
    )

    with pytest.raises(ValueError, match="token_usage must match"):
        LLMInteractionEvent(
            query_id="qry-1",
            trace_id="trc-1",
            request_timestamp=_ts(10, 0),
            response_timestamp=_ts(10, 1),
            prompt_text="hello",
            response_text="world",
            model_context=_context(),
            token_usage=bad_token_usage,
            latency=_latency(),
        )


def test_contract_version_validation() -> None:
    with pytest.raises(ValueError, match="Unsupported contract_version"):
        ModelExecutionContext(
            query_id="qry-1",
            trace_id="trc-1",
            model_version="gpt-5.4",
            dataset_version=None,
            provider="openai",
            model_name="gpt-5.4-mini",
            contract_version="2.0",
        )

    assert OBSERVABILITY_CONTRACT_VERSION == "1.0"
