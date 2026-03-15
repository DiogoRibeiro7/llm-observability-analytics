import sys

from llm_observability_analytics.cli.main import build_parser, main


def test_cli_parser_accepts_expected_flags() -> None:
    parser = build_parser()
    parsed = parser.parse_args(["--dry-run", "--config", "configs/base.yaml"])
    assert parsed.dry_run is True
    assert parsed.config.endswith("base.yaml")


def test_cli_main_dry_run(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(sys, "argv", ["llm-observability", "--dry-run", "--config", "cfg.yaml"])
    assert main() == 0
    assert "Dry run successful. Config: cfg.yaml" in capsys.readouterr().out


def test_cli_main_default_path(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(sys, "argv", ["llm-observability"])
    assert main() == 0
    assert "Event processing is not implemented yet." in capsys.readouterr().out
