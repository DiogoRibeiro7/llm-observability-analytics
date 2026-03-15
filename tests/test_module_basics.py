from __future__ import annotations

from datetime import UTC, datetime

import pytest

from llm_observability_analytics.contracts.entities import EventEnvelope
from llm_observability_analytics.contracts.models import UserFeedbackEvent
from llm_observability_analytics.events.interfaces import EventSink
from llm_observability_analytics.metrics.models import AnalyticsSummary, MetricRecord
from llm_observability_analytics.reports.specs import ReportSpec
from llm_observability_analytics.storage.interfaces import EventStore
from llm_observability_analytics.traces.models import TraceReference


def test_simple_dataclasses_and_serialization() -> None:
    metric = MetricRecord(
        metric_name="latency_mean_ms",
        metric_value=123.4,
        dimension_key="model",
        dimension_value="gpt-5.4-mini",
    )
    assert metric.metric_name == "latency_mean_ms"

    summary = AnalyticsSummary(
        request_count=10,
        retrieval_trace_count=8,
        latency_mean_ms=123.4,
        latency_p50_ms=100.0,
        latency_p95_ms=200.0,
        total_tokens=1200,
        average_tokens_per_request=120.0,
        retrieval_hit_count=7,
        grounded_response_count=6,
        ungrounded_response_count=4,
        feedback_count=2,
    )
    payload = summary.to_dict()
    assert payload["request_count"] == 10
    assert "latency_mean_ms" in summary.to_json()

    report = ReportSpec(report_name="daily", period_start="2026-01-01", period_end="2026-01-02")
    trace = TraceReference(trace_id="trc-1", query_id="qry-1")
    assert report.report_name == "daily"
    assert trace.trace_id == "trc-1"


def test_event_envelope_alias_accepts_contract_models() -> None:
    feedback = UserFeedbackEvent(
        query_id="qry-1",
        trace_id="trc-1",
        feedback_timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        feedback_label="thumbs_up",
    )
    envelope: EventEnvelope = feedback
    assert envelope.trace_id == "trc-1"


def test_abstract_interface_contracts() -> None:
    with pytest.raises(TypeError):
        EventSink()

    with pytest.raises(TypeError):
        EventStore()

    class InMemorySink(EventSink):
        def __init__(self) -> None:
            self.events: list[EventEnvelope] = []

        def emit(self, event: EventEnvelope) -> None:
            self.events.append(event)

    class InMemoryStore(EventStore):
        def __init__(self) -> None:
            self.payloads: list[dict[str, object]] = []

        def write(self, payload: dict[str, object]) -> None:
            self.payloads.append(payload)

    sink = InMemorySink()
    store = InMemoryStore()
    sink.emit(
        UserFeedbackEvent(
            query_id="qry-2",
            trace_id="trc-2",
            feedback_timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            feedback_label="thumbs_down",
        )
    )
    store.write({"k": "v"})
    assert len(sink.events) == 1
    assert store.payloads[0]["k"] == "v"
