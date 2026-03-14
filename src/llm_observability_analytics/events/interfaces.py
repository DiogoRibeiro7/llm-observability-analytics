from __future__ import annotations

from abc import ABC, abstractmethod

from llm_observability_analytics.contracts.entities import EventEnvelope


class EventSink(ABC):
    """Contract for event ingestion sinks."""

    @abstractmethod
    def emit(self, event: EventEnvelope) -> None:
        """Persist one event to a storage or transport backend."""
