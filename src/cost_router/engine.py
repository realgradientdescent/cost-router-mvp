from __future__ import annotations

from pathlib import Path

from .config import DEFAULT_CONFIG_PATH, load_provider_tiers
from .logger import decision_to_dict, log_decision
from .models import RoutingRequest
from .router import route_request

DEFAULT_LOG_PATH = Path("logs/router-decisions.jsonl")


def process_request_payload(
    payload: dict,
    log_path: Path | None = None,
    config_path: Path | None = None,
) -> dict:
    request = RoutingRequest.from_dict(payload)
    policy_version, provider_tiers = load_provider_tiers(config_path or DEFAULT_CONFIG_PATH)
    decision = route_request(request, provider_tiers=provider_tiers, policy_version=policy_version)
    resolved_log_path = log_path or DEFAULT_LOG_PATH
    log_decision(request, decision, resolved_log_path)
    return decision_to_dict(decision)
