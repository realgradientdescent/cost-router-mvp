from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ALLOWED_USER_TIERS = {"default", "power", "internal"}
ALLOWED_TASK_TYPES = {
    "classification",
    "summarization",
    "rewrite",
    "research",
    "code_generation",
    "code_debugging",
    "planning",
    "tool_calling",
    "data_extraction",
    "agent_orchestration",
}
ALLOWED_LEVELS = {"low", "medium", "high"}
ALLOWED_OVERRIDES = {None, "cheap", "premium"}


@dataclass
class RoutingRequest:
    request_id: str
    timestamp: str
    user_tier: str
    task_type: str
    task_goal: str
    max_latency_ms: int
    max_budget_usd: float
    requires_tools: bool
    requires_code_execution: bool
    needs_strict_json: bool
    needs_long_context: bool
    risk_level: str
    impact_level: str
    user_override: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RoutingRequest":
        required = [
            "request_id",
            "timestamp",
            "user_tier",
            "task_type",
            "task_goal",
            "max_latency_ms",
            "max_budget_usd",
            "requires_tools",
            "requires_code_execution",
            "needs_strict_json",
            "needs_long_context",
            "risk_level",
            "impact_level",
        ]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        request = cls(
            request_id=str(data["request_id"]),
            timestamp=str(data["timestamp"]),
            user_tier=str(data["user_tier"]),
            task_type=str(data["task_type"]),
            task_goal=str(data["task_goal"]),
            max_latency_ms=int(data["max_latency_ms"]),
            max_budget_usd=float(data["max_budget_usd"]),
            requires_tools=bool(data["requires_tools"]),
            requires_code_execution=bool(data["requires_code_execution"]),
            needs_strict_json=bool(data["needs_strict_json"]),
            needs_long_context=bool(data["needs_long_context"]),
            risk_level=str(data["risk_level"]),
            impact_level=str(data["impact_level"]),
            user_override=data.get("user_override"),
            metadata=data.get("metadata", {}),
        )
        request.validate()
        return request

    def validate(self) -> None:
        if self.user_tier not in ALLOWED_USER_TIERS:
            raise ValueError(f"Invalid user_tier: {self.user_tier}")
        if self.task_type not in ALLOWED_TASK_TYPES:
            raise ValueError(f"Invalid task_type: {self.task_type}")
        if self.risk_level not in ALLOWED_LEVELS:
            raise ValueError(f"Invalid risk_level: {self.risk_level}")
        if self.impact_level not in ALLOWED_LEVELS:
            raise ValueError(f"Invalid impact_level: {self.impact_level}")
        if self.user_override not in ALLOWED_OVERRIDES:
            raise ValueError(f"Invalid user_override: {self.user_override}")
        if self.max_latency_ms <= 0:
            raise ValueError("max_latency_ms must be > 0")
        if self.max_budget_usd < 0:
            raise ValueError("max_budget_usd must be >= 0")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be an object")


@dataclass
class ProviderTarget:
    route_name: str
    candidate_model_tier: str
    provider: str
    model: str
    notes: str = ""


@dataclass
class RoutingDecision:
    request_id: str
    selected_route: str
    candidate_model_tier: str
    selected_provider: str
    selected_model: str
    provider_routing_key: str
    policy_version: str
    reasons: list[str]
    estimated_cost_bucket: str
    estimated_latency_bucket: str
    logged_at: str
