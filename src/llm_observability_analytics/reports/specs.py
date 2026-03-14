from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReportSpec:
    report_name: str
    period_start: str
    period_end: str
