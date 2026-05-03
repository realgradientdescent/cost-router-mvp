# Cost Router MVP — Input Schema and Routing Rules

## Goal

Route agent workloads to the cheapest acceptable model path by default, while escalating to a premium path only when task characteristics justify it.

This MVP is intentionally deterministic and logging-first.

## Routing modes

- `cheap_default`
  - default path for low-risk, low-complexity, non-critical tasks
  - intended future target: smaller / cheaper open-weight or API model
- `premium_fallback`
  - escalation path for higher-risk, higher-complexity, or user-critical tasks
  - intended future target: stronger model with better reasoning / reliability

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
- `user_override`: optional explicit routing instruction
  - `cheap`
  - `premium`
  - `null`
- `metadata`: free-form object for logging only

## MVP routing rules

### Rule 0 — explicit user override wins

If `user_override == "premium"`:
- route to `premium_fallback`
- reason: `user_override_premium`

If `user_override == "cheap"`:
- route to `cheap_default`
- reason: `user_override_cheap`

### Rule 1 — high-risk or high-impact escalates

Route to `premium_fallback` when either is true:
- `risk_level == "high"`
- `impact_level == "high"`

Reason examples:
- `high_risk`
- `high_impact`

### Rule 2 — hard tasks escalate

Route to `premium_fallback` when either is true:
- `task_type in {"code_debugging", "agent_orchestration", "research"}`
- `requires_code_execution == true`

Reason examples:
- `hard_task_type`
- `requires_code_execution`

### Rule 3 — complex output constraints escalate

Route to `premium_fallback` when either is true:
- `needs_long_context == true`
- `needs_strict_json == true and task_type in {"tool_calling", "data_extraction", "agent_orchestration"}`

Reason examples:
- `needs_long_context`
- `strict_json_critical`

### Rule 4 — premium if cheap path is unlikely to meet budget/latency tradeoff

Route to `premium_fallback` when both are true:
- `max_latency_ms <= 2000`
- `task_type in {"planning", "research", "code_generation", "code_debugging"}`

Reason:
- `tight_latency_for_complex_task`

### Rule 5 — otherwise cheap by default

If none of the escalation rules fire:
- route to `cheap_default`
- reason: `default_cheap_path`

## Decision output schema

```json
{
  "request_id": "req_001",
  "selected_route": "premium_fallback",
  "candidate_model_tier": "premium",
  "reasons": ["requires_code_execution", "hard_task_type"],
  "estimated_cost_bucket": "medium",
  "estimated_latency_bucket": "medium",
  "logged_at": "2026-05-03T00:00:01Z"
}
```

## Logging schema

Each decision is appended as one JSON object per line to a JSONL file.

```json
{
  "request_id": "req_001",
  "timestamp": "2026-05-03T00:00:00Z",
  "task_type": "code_generation",
  "selected_route": "premium_fallback",
  "candidate_model_tier": "premium",
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

## Why this MVP shape is good

- simple enough to ship in a day
- useful enough to produce real routing logs immediately
- extensible to future provider adapters
- creates a clean training set for later policy tuning

## Next build after this MVP

1. swap route tiers for actual provider/model IDs
2. add real token/cost estimation
3. capture outcome quality and retries
4. add a replay/evaluation harness
5. learn thresholds from logs instead of hand-tuning only
