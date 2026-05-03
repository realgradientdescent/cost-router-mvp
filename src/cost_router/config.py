from __future__ import annotations

import json
from pathlib import Path

from .models import ProviderTarget

DEFAULT_CONFIG_PATH = Path("config/provider_tiers.json")


def load_provider_tiers(config_path: Path | None = None) -> tuple[str, dict[str, ProviderTarget]]:
    path = config_path or DEFAULT_CONFIG_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    policy_version = str(payload.get("policy_version", "mvp-v2"))
    tiers = payload.get("tiers", {})
    if not isinstance(tiers, dict) or not tiers:
        raise ValueError("provider tier config must define a non-empty 'tiers' object")

    resolved: dict[str, ProviderTarget] = {}
    for route_name, route_data in tiers.items():
        resolved[route_name] = ProviderTarget(
            route_name=route_name,
            candidate_model_tier=str(route_data["candidate_model_tier"]),
            provider=str(route_data["provider"]),
            model=str(route_data["model"]),
            notes=str(route_data.get("notes", "")),
        )
    return policy_version, resolved
