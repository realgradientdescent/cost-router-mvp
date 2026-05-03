from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import DEFAULT_CONFIG_PATH
from .engine import DEFAULT_LOG_PATH, process_request_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Route a task request to a model tier and log the decision.")
    parser.add_argument("request_path", help="Path to request JSON file")
    parser.add_argument("--log-path", default=str(DEFAULT_LOG_PATH), help="JSONL log output path")
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH), help="Provider tier config path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv or sys.argv[1:])

    try:
        request_path = Path(args.request_path)
        payload = json.loads(request_path.read_text(encoding="utf-8"))
        decision = process_request_payload(
            payload,
            log_path=Path(args.log_path),
            config_path=Path(args.config_path),
        )
        print(json.dumps(decision, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
