from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class EventInputSettings:
    interactions_path: Path
    retrievals_path: Path
    max_events: int = 1000

    def __post_init__(self) -> None:
        if self.max_events <= 0:
            raise ValueError("events.max_events must be > 0")


@dataclass(frozen=True, slots=True)
class OutputSettings:
    validated_events_path: Path
    summary_path: Path
    run_result_path: Path


@dataclass(frozen=True, slots=True)
class PipelineConfig:
    events: EventInputSettings
    output: OutputSettings


def _path(base_dir: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base_dir / candidate)


def _require_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Config key '{key}' must be a mapping")
    return value


def load_config(config_path: Path) -> PipelineConfig:
    base_dir = config_path.resolve().parent
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Config payload must be a mapping")

    events_data = _require_mapping(payload, "events")
    output_data = _require_mapping(payload, "output")

    events = EventInputSettings(
        interactions_path=_path(base_dir, str(events_data["interactions_path"])),
        retrievals_path=_path(base_dir, str(events_data["retrievals_path"])),
        max_events=int(events_data.get("max_events", 1000)),
    )
    output = OutputSettings(
        validated_events_path=_path(base_dir, str(output_data["validated_events_path"])),
        summary_path=_path(base_dir, str(output_data["summary_path"])),
        run_result_path=_path(base_dir, str(output_data["run_result_path"])),
    )
    return PipelineConfig(events=events, output=output)
