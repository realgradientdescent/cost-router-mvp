# Cost Router MVP — Portfolio Case Study

## One-line summary

Built a logging-first control-plane MVP that routes AI/agent workloads to the cheapest acceptable model tier by default, escalates to a premium fallback when task risk or complexity justifies it, resolves the route to specific provider/model targets, and exposes the same logic through both CLI and HTTP surfaces.

## Why I built this

A lot of AI products still hard-code one model per workflow.

That is a bad long-term posture.

As model quality converges and pricing pressure increases, the leverage shifts away from “pick one best model” and toward **control-plane logic**:
- when to use a cheaper model
- when to pay for a stronger one
- how to make the decision explicit
- how to log it so policy can improve over time

This project was a small but concrete step in that direction.

## The problem

If every task goes to a premium model:
- cost balloons unnecessarily
- latency often gets worse than it needs to be
- simple tasks subsidize complex ones with no discipline

If every task goes to a cheap model:
- quality breaks on harder reasoning work
- debugging and orchestration flows become fragile
- high-impact tasks get underpowered

The real product problem is not just model selection. It is **routing policy under tradeoffs**.

## What I built

### 1. Stable task input schema

I defined a routing request contract that captures the signals a control plane actually needs:
- task type
- latency budget
- budget cap
- risk level
- impact level
- code-execution requirement
- strict JSON requirement
- long-context need
- user override

That makes the routing policy explicit instead of hiding it inside prompts or ad hoc conditionals.

### 2. Deterministic routing policy

The router chooses between:
- `cheap_default`
- `premium_fallback`

Premium escalation happens for:
- high-risk tasks
- high-impact tasks
- harder task classes like debugging or orchestration
- code-execution-dependent work
- long-context or critical structured-output constraints
- tight latency budgets for complex task types

Otherwise the system stays cheap by default.

### 3. Provider/model resolution layer

I separated **policy** from **provider choice**.

Instead of stopping at “cheap vs premium,” the system resolves the selected route through `config/provider_tiers.json` into a real target.

Current example mapping:
- `cheap_default` → `openrouter : mistralai/mistral-small-3.1`
- `premium_fallback` → `anthropic : claude-sonnet-4`

That means routing logic can evolve independently from vendor decisions.

### 4. Shared execution path for CLI and API

I pulled the routing flow into a shared engine so two different surfaces use the same core behavior:
- CLI for local experiments and scripts
- FastAPI service for integration as a small internal platform primitive

That is a subtle but important design choice: the system is not a one-off demo command. It is starting to behave like reusable infrastructure.

### 5. Logging-first observability

Every decision is appended to `logs/router-decisions.jsonl`.

That log becomes the seed dataset for:
- replay testing
- routing analytics
- threshold tuning
- future learned policy
- cost/latency evaluation

This was intentional. I wanted the MVP to generate the evidence required for the next version, not just produce a single good-looking output.

## What I verified

This repo was not left at the “should work” stage.

I verified:
- the CLI path with real example payloads
- resolved provider/model outputs for both cheap and premium paths
- zero-dependency unit tests (`5/5` passing)
- FastAPI endpoints:
  - `GET /health`
  - `GET /tiers`
  - `POST /route`

I also generated portfolio-grade evidence assets:
- a live routing evidence visual
- a control-plane architecture diagram

## Architecture and evidence

### Live routing evidence

![Live routing evidence](../evidence/screenshots/routing-decision-demo.svg)

### Control-plane architecture

![Control-plane architecture](../evidence/diagrams/cost-router-architecture.svg)

## Technical decisions that matter

### Separation of concerns

I explicitly separated:
- request validation
- routing policy
- provider/model mapping
- delivery surfaces
- observability

That structure matters because it prevents the common failure mode where routing logic gets entangled with provider integration code.

### Logging before optimization

Most AI demos jump straight to “smart” behavior without building the audit trail needed to improve it.

I chose the opposite sequence:
1. make policy deterministic
2. make decisions inspectable
3. log everything
4. improve the policy later from evidence

That is slower in the first hour, but much better by week two.

### Honest environment handling

The container environment used for verification did not have normal `pip` / `venv` workflows available on system Python.

Instead of pretending the standard local setup worked, I verified the FastAPI service using the existing Hermes runtime that already included FastAPI and uvicorn.

That sounds small, but it is actually a meaningful engineering habit: keep the repo docs honest to the environment you *actually* proved.

## What this project demonstrates about me

This repo shows more than “I can call an LLM.”

It shows that I think in terms of:
- product tradeoffs, not just implementation
- cost/latency/quality balancing
- reusable control planes instead of one-off workflows
- observability as a first-class design concern
- staged system evolution from heuristics to learned policy

That combination is especially relevant for agent infrastructure, internal AI platforms, and product-minded ML systems work.

## What I would build next

If I kept pushing this, the next high-leverage steps would be:
1. token and cost estimation
2. real provider adapters behind the route targets
3. replay/eval harness over logged requests
4. task outcome capture to compare routing decisions against actual success
5. threshold tuning or learned policy on top of the log history

## Repo pointers

- [README](../README.md)
- [Schema and routing rules](input-schema-and-routing-rules.md)
- [Architecture diagram](../evidence/diagrams/cost-router-architecture.svg)
- [Live routing evidence](../evidence/screenshots/routing-decision-demo.svg)
