# Contract Consistency Strategy

## Objective

Keep shared contract identifiers, field names, and handoff formats aligned across independent repositories:

- `llm-knowledge-ingestion`
- `llm-observability-analytics`
- `llm-dataset-foundry`

## Lightweight Mechanism

Each repository contains:

- `docs/shared-contract-summary.json` (machine-readable contract summary)
- `scripts/validate_shared_contracts.py` (manual validator)

The summary defines:

- canonical shared identifiers and semantics
- repository contract version references
- produced/consumed handoff artifacts and required fields
- example artifact paths used for field validation

## Manual Validation

Local check:

```bash
python scripts/validate_shared_contracts.py
```

Cross-repository alignment check (when sibling repos are available):

```bash
python scripts/validate_shared_contracts.py \
  --peer ../llm-observability-analytics/docs/shared-contract-summary.json \
  --peer ../llm-dataset-foundry/docs/shared-contract-summary.json
```

## Safe Update Process

1. Propose contract change in `docs/shared-contract-summary.json` first.
2. Update affected schemas/docs/examples in the same repo.
3. Run local validator.
4. Open coordinated PRs in other repositories.
5. Update peer summaries and integration examples.
6. Run cross-repo validation using `--peer` before merge.
7. Record breaking changes with explicit version bump and migration notes.
