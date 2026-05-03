import json
import unittest
from pathlib import Path

from src.cost_router.cli import main
from src.cost_router.models import RoutingRequest
from src.cost_router.router import route_request


def load_example(name: str) -> RoutingRequest:
    path = Path("examples") / name
    return RoutingRequest.from_dict(json.loads(path.read_text(encoding="utf-8")))


class RouterTests(unittest.TestCase):
    def test_simple_task_routes_to_cheap_default(self):
        request = load_example("simple-task.json")
        decision = route_request(request)
        self.assertEqual(decision.selected_route, "cheap_default")
        self.assertEqual(decision.reasons, ["default_cheap_path"])

    def test_code_debugging_routes_to_premium(self):
        request = load_example("premium-task.json")
        decision = route_request(request)
        self.assertEqual(decision.selected_route, "premium_fallback")
        self.assertIn("hard_task_type", decision.reasons)
        self.assertIn("requires_code_execution", decision.reasons)
        self.assertIn("high_impact", decision.reasons)

    def test_user_override_cheap_wins(self):
        request = load_example("premium-task.json")
        request.user_override = "cheap"
        decision = route_request(request)
        self.assertEqual(decision.selected_route, "cheap_default")
        self.assertEqual(decision.reasons, ["user_override_cheap"])

    def test_cli_writes_log_file(self):
        log_path = Path("tests/tmp-router-decisions.jsonl")
        if log_path.exists():
            log_path.unlink()
        exit_code = main(["examples/simple-task.json", str(log_path)])
        self.assertEqual(exit_code, 0)
        self.assertTrue(log_path.exists())
        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        payload = json.loads(lines[0])
        self.assertEqual(payload["request_id"], "req_simple_001")
        self.assertEqual(payload["selected_route"], "cheap_default")
        log_path.unlink()


if __name__ == "__main__":
    unittest.main()
