from __future__ import annotations

from datetime import UTC, datetime

from .models import RoutingDecision, RoutingRequest

HARD_TASK_TYPES = {"code_debugging", "agent_orchestration", "research"}
STRICT_JSON_PREMIUM_TYPES = {"tool_calling", "data_extraction", "agent_orchestration"}
LATENCY_SENSITIVE_COMPLEX_TYPES = {"planning", "research", "code_generation", "code_debugging"}


def estimate_cost_bucket(request: RoutingRequest, route: str) -> str:
    if route == "premium_fallback":
        return "medium" if request.max_budget_usd >= 0.02 else "high"
    return "low"


def estimate_latency_bucket(request: RoutingRequest) -> str:
    if request.max_latency_ms <= 2000:
        return "low"
    if request.max_latency_ms <= 5000:
        return "medium"
    return "high"


def route_request(request: RoutingRequest) -> RoutingDecision:
    reasons: list[str] = []

    if request.user_override == "premium":
        reasons.append("user_override_premium")
        return _decision(request, "premium_fallback", "premium", reasons)

    if request.user_override == "cheap":
        reasons.append("user_override_cheap")
        return _decision(request, "cheap_default", "cheap", reasons)

    if request.risk_level == "high":
        reasons.append("high_risk")
    if request.impact_level == "high":
        reasons.append("high_impact")
    if request.task_type in HARD_TASK_TYPES:
        reasons.append("hard_task_type")
    if request.requires_code_execution:
        reasons.append("requires_code_execution")
    if request.needs_long_context:
        reasons.append("needs_long_context")
    if request.needs_strict_json and request.task_type in STRICT_JSON_PREMIUM_TYPES:
        reasons.append("strict_json_critical")
    if request.max_latency_ms <= 2000 and request.task_type in LATENCY_SENSITIVE_COMPLEX_TYPES:
        reasons.append("tight_latency_for_complex_task")

    if reasons:
        return _decision(request, "premium_fallback", "premium", reasons)

    return _decision(request, "cheap_default", "cheap", ["default_cheap_path"])


def _decision(
    request: RoutingRequest,
    selected_route: str,
    candidate_model_tier: str,
    reasons: list[str],
) -> RoutingDecision:
    return RoutingDecision(
        request_id=request.request_id,
        selected_route=selected_route,
        candidate_model_tier=candidate_model_tier,
        reasons=reasons,
        estimated_cost_bucket=estimate_cost_bucket(request, selected_route),
        estimated_latency_bucket=estimate_latency_bucket(request),
        logged_at=datetime.now(UTC).isoformat(),
    )
