# Integration

## Role in Platform Flow

`llm-observability-analytics` links ingestion artifacts to runtime LLM behavior.

Flow:

1. `llm-knowledge-ingestion` emits stable `document_id` and `chunk_id`.
2. Observability captures interaction and retrieval trace events referencing those IDs.
3. Observability emits analytics-ready event JSONL for `llm-dataset-foundry`.
4. `llm-dataset-foundry` builds prompt-response and retrieval-eval datasets from these traces.

## Upstream and Downstream Boundaries

Upstream:

- ingestion chunk/document artifacts
- runtime service telemetry

Downstream:

- dataset curation inputs (`interactions.jsonl`, `retrieval_traces.jsonl`)
- operational summaries and report payloads

## Expected Handoff Artifacts

Expected from `llm-knowledge-ingestion`:

- `chunks.jsonl` with `chunk_id`, `document_id`

Produced for `llm-dataset-foundry`:

- `interactions.jsonl` with `query_id`, `trace_id`, `prompt_text`, `response_text`, `model_context`, `retrieval_references`
- `retrieval_traces.jsonl` with `query_id`, `trace_id`, `references`, expected targets

## Example Integration Artifacts

See `examples/integration/`:

- `input_from_ingestion_chunks.jsonl`
- `output_for_dataset_foundry_interactions.jsonl`
- `output_for_dataset_foundry_retrieval_traces.jsonl`
