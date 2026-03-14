# Data Contracts

This repository defines runtime observability contracts aligned with platform identifiers.

## Shared Platform Identifiers

- `source_id`
- `document_id`
- `chunk_id`
- `query_id`
- `trace_id`
- `dataset_id` (downstream)
- `dataset_version`
- `model_version`

Contract constant:

- `OBSERVABILITY_CONTRACT_VERSION = "1.0"`

## Produced Schemas

### LLMInteractionEvent

Core fields:

- `query_id`
- `trace_id`
- `request_timestamp`
- `response_timestamp`
- `prompt_text`
- `response_text`
- `model_context`
- `token_usage`
- `latency`
- `retrieval_references`
- `feedback`
- `contract_version`

### RetrievalTraceEvent

Core fields:

- `query_id`
- `trace_id`
- `retrieval_timestamp`
- `query_text`
- `retrieval_system`
- `top_k`
- `references` (list with `document_id`, `chunk_id`, `rank`, `score`)
- `model_version`
- `dataset_version`
- `status`
- `contract_version`

### TokenUsageRecord and LatencyRecord

Core fields:

- token usage: `input_tokens`, `output_tokens`, `total_tokens`, `model_version`
- latency: `request_timestamp`, `response_timestamp`, `latency_ms`

### UserFeedbackEvent

Core fields:

- `query_id`
- `trace_id`
- `feedback_timestamp`
- feedback payload (`rating`, `feedback_text`, `feedback_label`)
- optional `model_version`, `dataset_version`

## Handoff Formats

- `interactions.jsonl`: handoff to `llm-dataset-foundry`
- `retrieval_traces.jsonl`: handoff to `llm-dataset-foundry`

Cross-repo linkage fields required in these handoffs:

- `query_id`
- `trace_id`
- `document_id` and `chunk_id` (inside retrieval references)
- `model_version`
- `dataset_version` (when available)
