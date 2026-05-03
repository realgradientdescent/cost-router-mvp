from __future__ import annotations

import json
import sys
from pathlib import Path

from .logger import decision_to_dict, log_decision
from .models import RoutingRequest
from .router import route_request

DEFAULT_LOG_PATH = Path("logs/router-decisions.jsonl")


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: python3 -m src.cost_router.cli <request.json> [log_path]", file=sys.stderr)
        return 2

    request_path = Path(argv[0])
    log_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_LOG_PATH

    try:
        payload = json.loads(request_path.read_text(encoding="utf-8"))
        request = RoutingRequest.from_dict(payload)
        decision = route_request(request)
        log_decision(request, decision, log_path)
        print(json.dumps(decision_to_dict(decision), indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
