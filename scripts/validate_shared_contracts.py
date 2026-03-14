from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CANONICAL_IDENTIFIERS: dict[str, str] = {
    "source_id": "Stable identifier of the upstream knowledge source.",
    "document_id": "Stable identifier of a normalized source document.",
    "chunk_id": "Stable identifier of a chunk derived from a document.",
    "query_id": "Identifier of a single user or system query request.",
    "trace_id": "Identifier grouping all events/spans in one execution trace.",
    "dataset_id": "Logical identifier of a curated dataset.",
    "dataset_version": "Immutable version of a curated dataset snapshot.",
    "model_version": "Explicit model version used to produce runtime outputs.",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object at {path}:{idx}")
        rows.append(payload)
    return rows


def _validate_identifiers(summary: dict[str, Any], errors: list[str]) -> None:
    identifiers = summary.get("identifiers")
    if not isinstance(identifiers, dict):
        errors.append("Missing object: identifiers")
        return

    actual = set(identifiers.keys())
    expected = set(CANONICAL_IDENTIFIERS.keys())
    if actual != expected:
        errors.append(f"Identifier key drift. expected={sorted(expected)} actual={sorted(actual)}")

    for key, expected_desc in CANONICAL_IDENTIFIERS.items():
        spec = identifiers.get(key)
        if not isinstance(spec, dict):
            errors.append(f"Identifier '{key}' must be an object")
            continue
        if spec.get("type") != "string":
            errors.append(f"Identifier '{key}' must declare type='string'")
        if spec.get("description") != expected_desc:
            errors.append(f"Identifier '{key}' description drifted from canonical text")


def _validate_handoffs(summary: dict[str, Any], repo_root: Path, errors: list[str]) -> None:
    handoffs = summary.get("handoffs")
    if not isinstance(handoffs, dict):
        errors.append("Missing object: handoffs")
        return

    for direction in ("produces", "consumes"):
        entries = handoffs.get(direction, [])
        if not isinstance(entries, list):
            errors.append(f"handoffs.{direction} must be a list")
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                errors.append(f"handoffs.{direction} contains non-object entry")
                continue
            name = str(entry.get("name", "<unknown>"))
            required_fields = entry.get("required_fields", [])
            if not isinstance(required_fields, list) or not required_fields:
                errors.append(f"handoff '{name}' must declare non-empty required_fields")
                continue
            example_rel = entry.get("example")
            if not isinstance(example_rel, str) or not example_rel:
                errors.append(f"handoff '{name}' must include example path")
                continue
            example = repo_root / example_rel
            if not example.exists():
                errors.append(f"handoff '{name}' example not found: {example_rel}")
                continue

            if example.suffix == ".jsonl":
                rows = _iter_jsonl(example)
                if not rows:
                    errors.append(f"handoff '{name}' example is empty: {example_rel}")
                    continue
                row = rows[0]
            elif example.suffix == ".json":
                payload = _load_json(example)
                row = payload if isinstance(payload, dict) else {}
            else:
                errors.append(f"handoff '{name}' example must be .json or .jsonl: {example_rel}")
                continue

            missing = [field for field in required_fields if field not in row]
            if missing:
                errors.append(f"handoff '{name}' example missing required fields: {missing}")


def _validate_version(summary: dict[str, Any], errors: list[str]) -> None:
    version = summary.get("shared_contract_version")
    if not isinstance(version, str) or not version.strip():
        errors.append("shared_contract_version must be a non-empty string")


def validate_summary(path: Path) -> list[str]:
    summary = _load_json(path)
    errors: list[str] = []
    _validate_version(summary, errors)
    _validate_identifiers(summary, errors)
    _validate_handoffs(summary, path.parent.parent, errors)
    return errors


def validate_peer_alignment(local_path: Path, peer_paths: list[Path]) -> list[str]:
    errors: list[str] = []
    local = _load_json(local_path)
    local_ids = local.get("identifiers", {})
    local_version = local.get("shared_contract_version")

    for peer_path in peer_paths:
        peer = _load_json(peer_path)
        peer_ids = peer.get("identifiers", {})
        peer_version = peer.get("shared_contract_version")
        if local_version != peer_version:
            errors.append(
                f"shared_contract_version mismatch: local={local_version} peer={peer_version} ({peer_path})"
            )
        if set(local_ids.keys()) != set(peer_ids.keys()):
            errors.append(f"identifier keys mismatch against peer: {peer_path}")
        for key in CANONICAL_IDENTIFIERS:
            local_desc = (local_ids.get(key) or {}).get("description")
            peer_desc = (peer_ids.get(key) or {}).get("description")
            if local_desc != peer_desc:
                errors.append(f"identifier description mismatch for '{key}' against peer: {peer_path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate shared contract consistency")
    parser.add_argument(
        "--summary",
        default="docs/shared-contract-summary.json",
        help="Path to local shared contract summary JSON",
    )
    parser.add_argument(
        "--peer",
        action="append",
        default=[],
        help="Path to a peer repository summary for cross-repo alignment checks",
    )
    args = parser.parse_args()

    summary_path = Path(args.summary)
    if not summary_path.exists():
        print(f"ERROR: summary file not found: {summary_path}")
        return 1

    errors = validate_summary(summary_path)
    peer_paths = [Path(p) for p in args.peer]
    if peer_paths:
        errors.extend(validate_peer_alignment(summary_path, peer_paths))

    if errors:
        print("Contract consistency check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Contract consistency check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
