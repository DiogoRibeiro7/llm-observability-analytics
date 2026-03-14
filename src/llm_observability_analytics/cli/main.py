from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llm-observability")
    parser.add_argument("--config", default="configs/base.yaml", help="Path to configuration file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and module wiring without processing events",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.dry_run:
        print(f"Dry run successful. Config: {args.config}")
        return 0

    print("Event processing is not implemented yet. Use --dry-run for validation mode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
