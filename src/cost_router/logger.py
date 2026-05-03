from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import RoutingDecision, RoutingRequest


def log_decision(request: RoutingRequest, decision: RoutingDecision, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "request_id": request.request_id,
        "timestamp": request.timestamp,
        "task_type": request.task_type,
        "selected_route": decision.selected_route,
        "candidate_model_tier": decision.candidate_model_tier,
        "reasons": decision.reasons,
        "max_latency_ms": request.max_latency_ms,
        "max_budget_usd": request.max_budget_usd,
        "risk_level": request.risk_level,
        "impact_level": request.impact_level,
        "metadata": request.metadata,
        "logged_at": decision.logged_at,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def decision_to_dict(decision: RoutingDecision) -> dict:
    return asdict(decision)
