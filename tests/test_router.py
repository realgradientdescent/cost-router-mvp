import json
import unittest
from pathlib import Path

from src.cost_router.cli import main
from src.cost_router.engine import process_request_payload
from src.cost_router.models import RoutingRequest
from src.cost_router.router import route_request
from src.cost_router.config import load_provider_tiers


def load_example(name: str) -> RoutingRequest:
    path = Path("examples") / name
    return RoutingRequest.from_dict(json.loads(path.read_text(encoding="utf-8")))


class RouterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy_version, cls.provider_tiers = load_provider_tiers(Path("config/provider_tiers.json"))

    def test_simple_task_routes_to_cheap_default(self):
        request = load_example("simple-task.json")
        decision = route_request(request, self.provider_tiers, self.policy_version)
        self.assertEqual(decision.selected_route, "cheap_default")
        self.assertEqual(decision.reasons, ["default_cheap_path"])
        self.assertEqual(decision.selected_provider, "openrouter")
        self.assertEqual(decision.selected_model, "mistralai/mistral-small-3.1")

    def test_code_debugging_routes_to_premium(self):
        request = load_example("premium-task.json")
        decision = route_request(request, self.provider_tiers, self.policy_version)
        self.assertEqual(decision.selected_route, "premium_fallback")
        self.assertIn("hard_task_type", decision.reasons)
        self.assertIn("requires_code_execution", decision.reasons)
        self.assertIn("high_impact", decision.reasons)
        self.assertEqual(decision.selected_provider, "anthropic")
        self.assertEqual(decision.selected_model, "claude-sonnet-4")

    def test_user_override_cheap_wins(self):
        request = load_example("premium-task.json")
        request.user_override = "cheap"
        decision = route_request(request, self.provider_tiers, self.policy_version)
        self.assertEqual(decision.selected_route, "cheap_default")
        self.assertEqual(decision.reasons, ["user_override_cheap"])
        self.assertEqual(decision.selected_provider, "openrouter")

    def test_engine_returns_provider_mapping(self):
        payload = json.loads(Path("examples/premium-task.json").read_text(encoding="utf-8"))
        decision = process_request_payload(
            payload,
            log_path=Path("tests/tmp-engine-router-decisions.jsonl"),
            config_path=Path("config/provider_tiers.json"),
        )
        self.assertEqual(decision["selected_route"], "premium_fallback")
        self.assertEqual(decision["selected_provider"], "anthropic")
        self.assertEqual(decision["policy_version"], "mvp-v2")
        Path("tests/tmp-engine-router-decisions.jsonl").unlink()

    def test_cli_writes_log_file(self):
        log_path = Path("tests/tmp-router-decisions.jsonl")
        if log_path.exists():
            log_path.unlink()
        exit_code = main([
            "examples/simple-task.json",
            "--log-path",
            str(log_path),
            "--config-path",
            "config/provider_tiers.json",
        ])
        self.assertEqual(exit_code, 0)
        self.assertTrue(log_path.exists())
        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        payload = json.loads(lines[0])
        self.assertEqual(payload["request_id"], "req_simple_001")
        self.assertEqual(payload["selected_route"], "cheap_default")
        self.assertEqual(payload["selected_provider"], "openrouter")
        log_path.unlink()


if __name__ == "__main__":
    unittest.main()
