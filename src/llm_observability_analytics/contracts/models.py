from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, cast

OBSERVABILITY_CONTRACT_VERSION = "1.0"
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$")


def _is_tz_aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.tzinfo.utcoffset(value) is not None


def _assert_non_empty(value: str, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be empty")


def _assert_id(value: str, name: str) -> None:
    _assert_non_empty(value, name)
    if not ID_PATTERN.fullmatch(value):
        raise ValueError(f"{name} must match {ID_PATTERN.pattern}")


def _assert_timestamp(value: datetime, name: str) -> None:
    if not _is_tz_aware(value):
        raise ValueError(f"{name} must be timezone-aware")


def _assert_contract_version(value: str) -> None:
    if value != OBSERVABILITY_CONTRACT_VERSION:
        raise ValueError(
            f"Unsupported contract_version={value!r}; expected {OBSERVABILITY_CONTRACT_VERSION!r}"
        )


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    return value


class ContractModel:
    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _serialize(asdict(cast(Any, self))))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass(frozen=True, slots=True)
class ModelExecutionContext(ContractModel):
    query_id: str
    trace_id: str
    model_version: str
    dataset_version: str | None
    provider: str
    model_name: str
    temperature: float | None = None
    max_tokens: int | None = None
    system_metadata: dict[str, str] = field(default_factory=dict)
    model_metadata: dict[str, str] = field(default_factory=dict)
    contract_version: str = OBSERVABILITY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _assert_id(self.query_id, "query_id")
        _assert_id(self.trace_id, "trace_id")
        _assert_non_empty(self.model_version, "model_version")
        _assert_non_empty(self.provider, "provider")
        _assert_non_empty(self.model_name, "model_name")
        if self.dataset_version is not None:
            _assert_non_empty(self.dataset_version, "dataset_version")
        if self.temperature is not None and not (0.0 <= self.temperature <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be > 0")
        _assert_contract_version(self.contract_version)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ModelExecutionContext:
        return cls(
            query_id=str(payload["query_id"]),
            trace_id=str(payload["trace_id"]),
            model_version=str(payload["model_version"]),
            dataset_version=payload.get("dataset_version"),
            provider=str(payload["provider"]),
            model_name=str(payload["model_name"]),
            temperature=cast(float | None, payload.get("temperature")),
            max_tokens=cast(int | None, payload.get("max_tokens")),
            system_metadata=dict(payload.get("system_metadata", {})),
            model_metadata=dict(payload.get("model_metadata", {})),
            contract_version=str(payload.get("contract_version", OBSERVABILITY_CONTRACT_VERSION)),
        )

    @classmethod
    def from_json(cls, payload: str) -> ModelExecutionContext:
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True, slots=True)
class SourceGroundingReference(ContractModel):
    query_id: str
    trace_id: str
    document_id: str
    chunk_id: str
    source_id: str | None = None
    dataset_version: str | None = None
    rank: int | None = None
    score: float | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    contract_version: str = OBSERVABILITY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _assert_id(self.query_id, "query_id")
        _assert_id(self.trace_id, "trace_id")
        _assert_id(self.document_id, "document_id")
        _assert_id(self.chunk_id, "chunk_id")
        if self.source_id is not None:
            _assert_id(self.source_id, "source_id")
        if self.dataset_version is not None:
            _assert_non_empty(self.dataset_version, "dataset_version")
        if self.rank is not None and self.rank < 0:
            raise ValueError("rank must be >= 0")
        if self.score is not None and self.score < 0:
            raise ValueError("score must be >= 0")
        _assert_contract_version(self.contract_version)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SourceGroundingReference:
        return cls(
            query_id=str(payload["query_id"]),
            trace_id=str(payload["trace_id"]),
            document_id=str(payload["document_id"]),
            chunk_id=str(payload["chunk_id"]),
            source_id=cast(str | None, payload.get("source_id")),
            dataset_version=cast(str | None, payload.get("dataset_version")),
            rank=cast(int | None, payload.get("rank")),
            score=cast(float | None, payload.get("score")),
            metadata=dict(payload.get("metadata", {})),
            contract_version=str(payload.get("contract_version", OBSERVABILITY_CONTRACT_VERSION)),
        )

    @classmethod
    def from_json(cls, payload: str) -> SourceGroundingReference:
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True, slots=True)
class TokenUsageRecord(ContractModel):
    query_id: str
    trace_id: str
    model_version: str
    dataset_version: str | None
    input_tokens: int
    output_tokens: int
    total_tokens: int | None = None
    billing_unit: str | None = None
    cost_estimate_usd: float | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    contract_version: str = OBSERVABILITY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _assert_id(self.query_id, "query_id")
        _assert_id(self.trace_id, "trace_id")
        _assert_non_empty(self.model_version, "model_version")
        if self.dataset_version is not None:
            _assert_non_empty(self.dataset_version, "dataset_version")
        if self.input_tokens < 0:
            raise ValueError("input_tokens must be >= 0")
        if self.output_tokens < 0:
            raise ValueError("output_tokens must be >= 0")
        expected = self.input_tokens + self.output_tokens
        if self.total_tokens is None:
            object.__setattr__(self, "total_tokens", expected)
        elif self.total_tokens != expected:
            raise ValueError("total_tokens must equal input_tokens + output_tokens")
        if self.cost_estimate_usd is not None and self.cost_estimate_usd < 0:
            raise ValueError("cost_estimate_usd must be >= 0")
        _assert_timestamp(self.recorded_at, "recorded_at")
        _assert_contract_version(self.contract_version)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TokenUsageRecord:
        return cls(
            query_id=str(payload["query_id"]),
            trace_id=str(payload["trace_id"]),
            model_version=str(payload["model_version"]),
            dataset_version=cast(str | None, payload.get("dataset_version")),
            input_tokens=int(payload["input_tokens"]),
            output_tokens=int(payload["output_tokens"]),
            total_tokens=cast(int | None, payload.get("total_tokens")),
            billing_unit=cast(str | None, payload.get("billing_unit")),
            cost_estimate_usd=cast(float | None, payload.get("cost_estimate_usd")),
            recorded_at=datetime.fromisoformat(str(payload["recorded_at"])),
            contract_version=str(payload.get("contract_version", OBSERVABILITY_CONTRACT_VERSION)),
        )

    @classmethod
    def from_json(cls, payload: str) -> TokenUsageRecord:
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True, slots=True)
class LatencyRecord(ContractModel):
    query_id: str
    trace_id: str
    request_timestamp: datetime
    response_timestamp: datetime
    latency_ms: int
    stage: str = "end_to_end"
    metadata: dict[str, str] = field(default_factory=dict)
    contract_version: str = OBSERVABILITY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _assert_id(self.query_id, "query_id")
        _assert_id(self.trace_id, "trace_id")
        _assert_timestamp(self.request_timestamp, "request_timestamp")
        _assert_timestamp(self.response_timestamp, "response_timestamp")
        if self.response_timestamp < self.request_timestamp:
            raise ValueError("response_timestamp must be >= request_timestamp")
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be >= 0")
        _assert_non_empty(self.stage, "stage")
        _assert_contract_version(self.contract_version)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> LatencyRecord:
        return cls(
            query_id=str(payload["query_id"]),
            trace_id=str(payload["trace_id"]),
            request_timestamp=datetime.fromisoformat(str(payload["request_timestamp"])),
            response_timestamp=datetime.fromisoformat(str(payload["response_timestamp"])),
            latency_ms=int(payload["latency_ms"]),
            stage=str(payload.get("stage", "end_to_end")),
            metadata=dict(payload.get("metadata", {})),
            contract_version=str(payload.get("contract_version", OBSERVABILITY_CONTRACT_VERSION)),
        )

    @classmethod
    def from_json(cls, payload: str) -> LatencyRecord:
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True, slots=True)
class UserFeedbackEvent(ContractModel):
    query_id: str
    trace_id: str
    feedback_timestamp: datetime
    rating: int | None = None
    feedback_text: str | None = None
    feedback_label: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    model_version: str | None = None
    dataset_version: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    contract_version: str = OBSERVABILITY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _assert_id(self.query_id, "query_id")
        _assert_id(self.trace_id, "trace_id")
        _assert_timestamp(self.feedback_timestamp, "feedback_timestamp")
        if self.rating is not None and not (1 <= self.rating <= 5):
            raise ValueError("rating must be between 1 and 5")
        if self.feedback_text is not None and not self.feedback_text.strip():
            raise ValueError("feedback_text must not be empty when set")
        if self.feedback_label is not None and not self.feedback_label.strip():
            raise ValueError("feedback_label must not be empty when set")
        if self.user_id is not None and not self.user_id.strip():
            raise ValueError("user_id must not be empty when set")
        if self.session_id is not None and not self.session_id.strip():
            raise ValueError("session_id must not be empty when set")
        if self.model_version is not None and not self.model_version.strip():
            raise ValueError("model_version must not be empty when set")
        if self.dataset_version is not None and not self.dataset_version.strip():
            raise ValueError("dataset_version must not be empty when set")
        if self.rating is None and self.feedback_text is None and self.feedback_label is None:
            raise ValueError("At least one of rating, feedback_text, or feedback_label is required")
        _assert_contract_version(self.contract_version)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> UserFeedbackEvent:
        return cls(
            query_id=str(payload["query_id"]),
            trace_id=str(payload["trace_id"]),
            feedback_timestamp=datetime.fromisoformat(str(payload["feedback_timestamp"])),
            rating=cast(int | None, payload.get("rating")),
            feedback_text=cast(str | None, payload.get("feedback_text")),
            feedback_label=cast(str | None, payload.get("feedback_label")),
            user_id=cast(str | None, payload.get("user_id")),
            session_id=cast(str | None, payload.get("session_id")),
            model_version=cast(str | None, payload.get("model_version")),
            dataset_version=cast(str | None, payload.get("dataset_version")),
            metadata=dict(payload.get("metadata", {})),
            contract_version=str(payload.get("contract_version", OBSERVABILITY_CONTRACT_VERSION)),
        )

    @classmethod
    def from_json(cls, payload: str) -> UserFeedbackEvent:
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True, slots=True)
class RetrievalTraceEvent(ContractModel):
    query_id: str
    trace_id: str
    retrieval_timestamp: datetime
    query_text: str
    retrieval_system: str
    top_k: int
    references: list[SourceGroundingReference] = field(default_factory=list)
    model_version: str | None = None
    dataset_version: str | None = None
    status: str = "ok"
    metadata: dict[str, str] = field(default_factory=dict)
    contract_version: str = OBSERVABILITY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _assert_id(self.query_id, "query_id")
        _assert_id(self.trace_id, "trace_id")
        _assert_timestamp(self.retrieval_timestamp, "retrieval_timestamp")
        _assert_non_empty(self.query_text, "query_text")
        _assert_non_empty(self.retrieval_system, "retrieval_system")
        if self.top_k < 0:
            raise ValueError("top_k must be >= 0")
        if self.model_version is not None:
            _assert_non_empty(self.model_version, "model_version")
        if self.dataset_version is not None:
            _assert_non_empty(self.dataset_version, "dataset_version")
        if not self.status.strip():
            raise ValueError("status must not be empty")
        for reference in self.references:
            if reference.query_id != self.query_id or reference.trace_id != self.trace_id:
                raise ValueError("references must match parent query_id and trace_id")
        _assert_contract_version(self.contract_version)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RetrievalTraceEvent:
        refs = [
            item if isinstance(item, SourceGroundingReference) else SourceGroundingReference.from_dict(item)
            for item in payload.get("references", [])
        ]
        return cls(
            query_id=str(payload["query_id"]),
            trace_id=str(payload["trace_id"]),
            retrieval_timestamp=datetime.fromisoformat(str(payload["retrieval_timestamp"])),
            query_text=str(payload["query_text"]),
            retrieval_system=str(payload["retrieval_system"]),
            top_k=int(payload["top_k"]),
            references=refs,
            model_version=cast(str | None, payload.get("model_version")),
            dataset_version=cast(str | None, payload.get("dataset_version")),
            status=str(payload.get("status", "ok")),
            metadata=dict(payload.get("metadata", {})),
            contract_version=str(payload.get("contract_version", OBSERVABILITY_CONTRACT_VERSION)),
        )

    @classmethod
    def from_json(cls, payload: str) -> RetrievalTraceEvent:
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True, slots=True)
class LLMInteractionEvent(ContractModel):
    query_id: str
    trace_id: str
    request_timestamp: datetime
    response_timestamp: datetime
    prompt_text: str
    response_text: str
    model_context: ModelExecutionContext
    token_usage: TokenUsageRecord
    latency: LatencyRecord
    retrieval_references: list[SourceGroundingReference] = field(default_factory=list)
    user_metadata: dict[str, str] = field(default_factory=dict)
    session_metadata: dict[str, str] = field(default_factory=dict)
    feedback: UserFeedbackEvent | None = None
    contract_version: str = OBSERVABILITY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _assert_id(self.query_id, "query_id")
        _assert_id(self.trace_id, "trace_id")
        _assert_timestamp(self.request_timestamp, "request_timestamp")
        _assert_timestamp(self.response_timestamp, "response_timestamp")
        if self.response_timestamp < self.request_timestamp:
            raise ValueError("response_timestamp must be >= request_timestamp")
        _assert_non_empty(self.prompt_text, "prompt_text")
        _assert_non_empty(self.response_text, "response_text")
        if self.model_context.query_id != self.query_id or self.model_context.trace_id != self.trace_id:
            raise ValueError("model_context must match parent query_id and trace_id")
        if self.token_usage.query_id != self.query_id or self.token_usage.trace_id != self.trace_id:
            raise ValueError("token_usage must match parent query_id and trace_id")
        if self.latency.query_id != self.query_id or self.latency.trace_id != self.trace_id:
            raise ValueError("latency must match parent query_id and trace_id")
        if self.token_usage.model_version != self.model_context.model_version:
            raise ValueError("token_usage.model_version must match model_context.model_version")
        for reference in self.retrieval_references:
            if reference.query_id != self.query_id or reference.trace_id != self.trace_id:
                raise ValueError("retrieval references must match parent query_id and trace_id")
        if self.feedback is not None:
            if self.feedback.query_id != self.query_id or self.feedback.trace_id != self.trace_id:
                raise ValueError("feedback must match parent query_id and trace_id")
        _assert_contract_version(self.contract_version)

    @property
    def model_version(self) -> str:
        return self.model_context.model_version

    @property
    def dataset_version(self) -> str | None:
        return self.model_context.dataset_version

    @property
    def latency_ms(self) -> int:
        return self.latency.latency_ms

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> LLMInteractionEvent:
        model_context = payload["model_context"]
        token_usage = payload["token_usage"]
        latency = payload["latency"]
        feedback = payload.get("feedback")
        references = payload.get("retrieval_references", [])
        return cls(
            query_id=str(payload["query_id"]),
            trace_id=str(payload["trace_id"]),
            request_timestamp=datetime.fromisoformat(str(payload["request_timestamp"])),
            response_timestamp=datetime.fromisoformat(str(payload["response_timestamp"])),
            prompt_text=str(payload["prompt_text"]),
            response_text=str(payload["response_text"]),
            model_context=(
                model_context
                if isinstance(model_context, ModelExecutionContext)
                else ModelExecutionContext.from_dict(model_context)
            ),
            token_usage=(
                token_usage
                if isinstance(token_usage, TokenUsageRecord)
                else TokenUsageRecord.from_dict(token_usage)
            ),
            latency=latency if isinstance(latency, LatencyRecord) else LatencyRecord.from_dict(latency),
            retrieval_references=[
                item
                if isinstance(item, SourceGroundingReference)
                else SourceGroundingReference.from_dict(item)
                for item in references
            ],
            user_metadata=dict(payload.get("user_metadata", {})),
            session_metadata=dict(payload.get("session_metadata", {})),
            feedback=(
                None
                if feedback is None
                else feedback
                if isinstance(feedback, UserFeedbackEvent)
                else UserFeedbackEvent.from_dict(feedback)
            ),
            contract_version=str(payload.get("contract_version", OBSERVABILITY_CONTRACT_VERSION)),
        )

    @classmethod
    def from_json(cls, payload: str) -> LLMInteractionEvent:
        return cls.from_dict(json.loads(payload))
