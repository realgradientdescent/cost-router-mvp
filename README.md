# Cost Router MVP

Logging-first local MVP for routing agent/LLM tasks to a cheap default model or premium fallback using deterministic rules.

## What this version does
- accepts a task request as JSON
- validates the input shape
- classifies routing risk/complexity with deterministic rules
- chooses a route: `cheap_default` or `premium_fallback`
- writes every decision to a local JSONL log
- prints the routing decision to stdout

## What this version does not do
- call real model providers
- retry or fail over network requests
- learn from outcomes automatically
- optimize routing based on live telemetry yet

## Quick start

```bash
cd /opt/data/workspace/cost-router-mvp
python3 -m src.cost_router.cli examples/simple-task.json
```

Run tests:

```bash
python3 -m pytest -q
```

## Project structure

- `docs/input-schema-and-routing-rules.md` — MVP contract and routing logic
- `src/cost_router/` — router implementation
- `tests/` — unit tests
- `examples/` — sample request payloads
- `logs/router-decisions.jsonl` — local decision ledger
