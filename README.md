# llm-observability-analytics

[![CI](https://github.com/DiogoRibeiro7/llm-observability-analytics/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/DiogoRibeiro7/llm-observability-analytics/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/DiogoRibeiro7/llm-observability-analytics/branch/develop/graph/badge.svg)](https://codecov.io/gh/DiogoRibeiro7/llm-observability-analytics)

Observability and analytics layer for a multi-repository LLM data engineering platform.

## Platform Position

`llm-observability-analytics` sits between ingestion outputs and dataset curation.
It remains an independent repository and provides runtime telemetry and derived analytics.

It explicitly integrates with:

- `llm-knowledge-ingestion` (upstream contract provider for `document_id`/`chunk_id`)
- `llm-dataset-foundry` (downstream consumer of curated interaction and retrieval traces)

## Upstream Inputs and Downstream Outputs

Upstream inputs:

- retrieval grounding context keyed by `document_id` and `chunk_id` from `llm-knowledge-ingestion`
- runtime prompt/response telemetry from serving systems

Downstream outputs:

- validated interaction events (`interactions.jsonl`)
- validated retrieval trace events (`retrieval_traces.jsonl`)
- analytics summaries and derived metrics

## Shared Identifiers

Produced and consumed:

- `query_id`
- `trace_id`
- `model_version`
- `dataset_version` (optional context)

Consumed from ingestion:

- `document_id`
- `chunk_id`
- `source_id`

## Why This Layer Exists

- correlate runtime behavior with source grounding
- compute latency/token/grounding quality metrics
- provide analytics-ready records for monitoring and dataset generation

## Integration References

- `docs/data-contracts.md`
- `docs/integration.md`
- `examples/integration/`

## Local Development

Prerequisites:

- Python 3.12+
- GNU Make (or equivalent direct commands)

Setup:

```bash
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e .[dev]
```

Common commands:

```bash
make format
make lint
make typecheck
make test
make ci
```

CLI:

```bash
python -m llm_observability_analytics.cli.main --dry-run --config configs/base.yaml
python -m llm_observability_analytics.cli.main --config configs/base.yaml
```


## Cross-Repo Consistency Checks

- Machine-readable summary: docs/shared-contract-summary.json`n- Manual validator: python scripts/validate_shared_contracts.py`n- Cross-repo check example:
  python scripts/validate_shared_contracts.py --peer ../llm-knowledge-ingestion/docs/shared-contract-summary.json --peer ../llm-dataset-foundry/docs/shared-contract-summary.json

