# Coordinated Release Process

This repository follows the platform release promotion model:

- `develop` is the default integration branch.
- `main` is the release branch and should remain protected.
- release tags are created only from `main`.

## Promotion Flow

1. Merge validated feature/fix PRs into `develop`.
2. Verify required checks pass on `develop` (`quality`, `codecov/patch`, contract checks).
3. Open a promotion PR from `develop` to `main`.
4. Merge to `main` only when promotion checklist is satisfied.
5. Trigger `Release From Main` workflow with a semantic version tag (`vX.Y.Z`).

## Coordination Across Repositories

For platform-level releases, promote the three repositories in a coordinated window:

- `llm-knowledge-ingestion`
- `llm-observability-analytics`
- `llm-dataset-foundry`

Recommended order:

1. ingestion
2. observability
3. dataset foundry

Use the same release milestone and changelog window across all three repositories.

## Release Checklist

- all release-scoped issues are closed or explicitly deferred
- contract summaries are aligned across repositories
- integration examples validate current handoff formats
- `main` branch protection is enabled and active
- release notes include contract-impact statements

## Workflow

The `.github/workflows/release-from-main.yml` workflow:

- validates tag format (`vX.Y.Z`)
- builds source and wheel distributions
- validates built artifacts with `twine check`
- creates Git tag and GitHub release with generated notes
