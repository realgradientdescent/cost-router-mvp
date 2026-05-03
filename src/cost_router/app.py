from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from .config import DEFAULT_CONFIG_PATH, load_provider_tiers
from .engine import DEFAULT_LOG_PATH, process_request_payload

app = FastAPI(title="Cost Router MVP", version="0.2.0")


def _config_path() -> Path:
    return Path(os.environ.get("COST_ROUTER_CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))


def _log_path() -> Path:
    return Path(os.environ.get("COST_ROUTER_LOG_PATH", str(DEFAULT_LOG_PATH)))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "cost-router-mvp"}


@app.get("/tiers")
def tiers() -> dict:
    policy_version, provider_tiers = load_provider_tiers(_config_path())
    return {
        "policy_version": policy_version,
        "tiers": {
            name: {
                "candidate_model_tier": target.candidate_model_tier,
                "provider": target.provider,
                "model": target.model,
                "notes": target.notes,
            }
            for name, target in provider_tiers.items()
        },
    }


@app.post("/route")
def route(payload: dict) -> dict:
    try:
        return process_request_payload(payload, log_path=_log_path(), config_path=_config_path())
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
