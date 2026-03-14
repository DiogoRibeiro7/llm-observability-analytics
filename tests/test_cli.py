from llm_observability_analytics.cli.main import build_parser


def test_cli_parser_accepts_expected_flags() -> None:
    parser = build_parser()
    parsed = parser.parse_args(["--dry-run", "--config", "configs/base.yaml"])
    assert parsed.dry_run is True
    assert parsed.config.endswith("base.yaml")
