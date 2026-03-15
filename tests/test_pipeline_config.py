from __future__ import annotations

from pathlib import Path

import pytest

from llm_observability_analytics.pipeline.config import EventInputSettings, load_config


def test_load_config_resolves_relative_paths(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
        events:
          interactions_path: data/interactions.jsonl
          retrievals_path: data/retrievals.jsonl
          max_events: 20
        output:
          validated_events_path: out/validated.jsonl
          summary_path: out/summary.json
          run_result_path: out/run_result.json
        """,
        encoding="utf-8",
    )

    cfg = load_config(cfg_path)
    assert cfg.events.interactions_path == tmp_path / "data" / "interactions.jsonl"
    assert cfg.events.retrievals_path == tmp_path / "data" / "retrievals.jsonl"
    assert cfg.events.max_events == 20
    assert cfg.output.summary_path == tmp_path / "out" / "summary.json"


def test_load_config_keeps_absolute_paths(tmp_path: Path) -> None:
    interactions = (tmp_path / "i.jsonl").resolve()
    retrievals = (tmp_path / "r.jsonl").resolve()
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        f"""
        events:
          interactions_path: {interactions}
          retrievals_path: {retrievals}
        output:
          validated_events_path: {tmp_path / 'v.jsonl'}
          summary_path: {tmp_path / 's.json'}
          run_result_path: {tmp_path / 'rr.json'}
        """,
        encoding="utf-8",
    )

    cfg = load_config(cfg_path)
    assert cfg.events.interactions_path == interactions
    assert cfg.events.retrievals_path == retrievals


def test_load_config_rejects_non_mapping_payload(tmp_path: Path) -> None:
    cfg_path = tmp_path / "bad.yaml"
    cfg_path.write_text("- just\n- a\n- list\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Config payload must be a mapping"):
        load_config(cfg_path)


def test_load_config_requires_events_and_output_mapping(tmp_path: Path) -> None:
    cfg_path = tmp_path / "bad.yaml"
    cfg_path.write_text(
        """
        events: []
        output: {}
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Config key 'events' must be a mapping"):
        load_config(cfg_path)


def test_event_settings_validate_positive_max_events() -> None:
    with pytest.raises(ValueError, match="events.max_events must be > 0"):
        EventInputSettings(
            interactions_path=Path("a"),
            retrievals_path=Path("b"),
            max_events=0,
        )
