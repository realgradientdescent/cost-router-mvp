# Cost Router MVP — Input Schema, Routing Rules, and API

## Goal

Route agent workloads to the cheapest acceptable model path by default, while escalating to a premium path only when the task profile justifies it.

This version is deliberately **deterministic, inspectable, and logging-first**.

## System contract

The MVP has three layers:

1. **Request schema** — what the caller must provide
2. **Routing policy** — how the system decides cheap vs premium
3. **Provider mapping** — how a route tier resolves to a specific provider/model target

That separation is the point.

## Route tiers

- `cheap_default`
  - intended for low-risk, low-complexity, low-cost tasks
- `premium_fallback`
  - intended for riskier or more complex tasks that justify a stronger model

## Provider mapping

Current mapping lives in:
- `config/provider_tiers.json`

Current defaults:

```json
{
  "policy_version": "mvp-v2",
  "tiers": {
    "cheap_default": {
      "candidate_model_tier": "cheap",
      "provider": "openrouter",
      "model": "mistralai/mistral-small-3.1"
    },
    "premium_fallback": {
      "candidate_model_tier": "premium",
      "provider": "anthropic",
      "model": "claude-sonnet-4"
    }
  }
}
```

## Input schema

Each routing request is a single JSON object.

```json
{
  "request_id": "req_001",
  "timestamp": "2026-05-03T00:00:00Z",
  "user_tier": "default",
  "task_type": "code_generation",
  "task_goal": "Implement a FastAPI endpoint for token usage reporting",
  "max_latency_ms": 5000,
  "max_budget_usd": 0.05,
  "requires_tools": true,
  "requires_code_execution": true,
  "needs_strict_json": false,
  "needs_long_context": false,
  "risk_level": "medium",
  "impact_level": "medium",
  "user_override": null,
  "metadata": {
    "source": "local-cli",
    "project": "cost-router-mvp"
  }
}
```

## Field definitions

- `request_id`: unique request identifier
- `timestamp`: ISO-8601 UTC timestamp
- `user_tier`: `default | power | internal`
- `task_type`:
  - `classification`
  - `summarization`
  - `rewrite`
  - `research`
  - `code_generation`
  - `code_debugging`
  - `planning`
  - `tool_calling`
  - `data_extraction`
  - `agent_orchestration`
- `task_goal`: short natural-language description of the job
- `max_latency_ms`: upper latency budget
- `max_budget_usd`: per-request budget cap
- `requires_tools`: whether downstream tool use is expected
- `requires_code_execution`: whether correctness depends on execution
- `needs_strict_json`: whether malformed output is costly
- `needs_long_context`: whether task likely needs large context windows
- `risk_level`: `low | medium | high`
- `impact_level`: `low | medium | high`
- `user_override`: optional explicit routing instruction: `cheap | premium | null`
- `metadata`: free-form object for logging only

## Routing rules

### Rule 0 — explicit user override wins

If `user_override == "premium"`:
- route to `premium_fallback`
- reason: `user_override_premium`

If `user_override == "cheap"`:
- route to `cheap_default`
- reason: `user_override_cheap`

### Rule 1 — high-risk or high-impact escalates

Escalate when either is true:
- `risk_level == "high"`
- `impact_level == "high"`

### Rule 2 — hard tasks escalate

Escalate when either is true:
- `task_type in {"code_debugging", "agent_orchestration", "research"}`
- `requires_code_execution == true`

### Rule 3 — output complexity escalates

Escalate when either is true:
- `needs_long_context == true`
- `needs_strict_json == true and task_type in {"tool_calling", "data_extraction", "agent_orchestration"}`

### Rule 4 — tight latency on complex work escalates

Escalate when both are true:
- `max_latency_ms <= 2000`
- `task_type in {"planning", "research", "code_generation", "code_debugging"}`

### Rule 5 — otherwise go cheap by default

If no escalation rule fires:
- route to `cheap_default`
- reason: `default_cheap_path`

## Decision output schema

```json
{
  "request_id": "req_001",
  "selected_route": "premium_fallback",
  "candidate_model_tier": "premium",
  "selected_provider": "anthropic",
  "selected_model": "claude-sonnet-4",
  "provider_routing_key": "anthropic:claude-sonnet-4",
  "policy_version": "mvp-v2",
  "reasons": ["requires_code_execution", "hard_task_type"],
  "estimated_cost_bucket": "medium",
  "estimated_latency_bucket": "medium",
  "logged_at": "2026-05-03T00:00:01Z"
}
```

## Logging schema

Each decision is appended as one JSON object per line to `logs/router-decisions.jsonl`.

```json
{
  "request_id": "req_001",
  "timestamp": "2026-05-03T00:00:00Z",
  "task_type": "code_generation",
  "selected_route": "premium_fallback",
  "candidate_model_tier": "premium",
  "selected_provider": "anthropic",
  "selected_model": "claude-sonnet-4",
  "provider_routing_key": "anthropic:claude-sonnet-4",
  "policy_version": "mvp-v2",
  "reasons": ["requires_code_execution"],
  "max_latency_ms": 5000,
  "max_budget_usd": 0.05,
  "risk_level": "medium",
  "impact_level": "medium",
  "metadata": {
    "source": "local-cli",
    "project": "cost-router-mvp"
  },
  "logged_at": "2026-05-03T00:00:01Z"
}
```

## API contract

### `GET /health`

Returns:

```json
{
  "status": "ok",
  "service": "cost-router-mvp"
}
```

### `GET /tiers`

Returns the currently loaded routing tier config.

### `POST /route`

Accepts the routing request JSON and returns the decision payload.

## Verification commands

Run CLI locally:

```bash
python3 -m src.cost_router.cli examples/premium-task.json --config-path config/provider_tiers.json
```

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

Run the API using the Hermes runtime that already includes FastAPI and uvicorn:

```bash
/opt/hermes/venv/bin/python -m uvicorn src.cost_router.app:app --host 127.0.0.1 --port 8000
```

Then verify:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/tiers
curl -X POST http://127.0.0.1:8000/route -H 'Content-Type: application/json' --data @examples/premium-task.json
```

## Why this design is good

- policy is explicit, reviewable, and testable
- provider choices can change without rewriting policy logic
- every decision is logged for later analytics and replay
- the same engine powers both CLI and HTTP surfaces

## High-value next steps

1. add real prompt/token estimation
2. plug in live provider/model adapters
3. attach task outcomes and retry data to each logged decision
4. build a replay/eval harness over real task traces
5. tune policy thresholds from observed performance instead of rules alone
