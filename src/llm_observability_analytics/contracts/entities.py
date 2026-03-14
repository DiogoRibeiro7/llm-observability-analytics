from __future__ import annotations

from llm_observability_analytics.contracts.models import (
    LLMInteractionEvent,
    RetrievalTraceEvent,
    UserFeedbackEvent,
)

EventEnvelope = LLMInteractionEvent | RetrievalTraceEvent | UserFeedbackEvent

__all__ = ["EventEnvelope", "LLMInteractionEvent", "RetrievalTraceEvent", "UserFeedbackEvent"]
