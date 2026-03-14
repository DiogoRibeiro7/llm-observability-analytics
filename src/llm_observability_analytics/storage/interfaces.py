from __future__ import annotations

from abc import ABC, abstractmethod


class EventStore(ABC):
    @abstractmethod
    def write(self, payload: dict[str, object]) -> None:
        """Write one observability record to storage."""
