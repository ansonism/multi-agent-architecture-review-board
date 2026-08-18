# Architecture

## Design goals

- Provider-neutral LLM layer
- Typed domain boundaries
- Explicit workflow state
- Tool isolation and least privilege
- Deterministic local mode
- Evidence-first results
- Human approval for production mutations
- Auditable execution

## Logical architecture

```mermaid
flowchart LR
  CLI[CLI/API] --> ORCH[Workflow Orchestrator]
  ORCH --> A[Specialist Agents]
  A --> P[LLM Provider Interface]
  A --> T[Typed Tool Adapters]
  ORCH --> E[Evidence + Risk Models]
  ORCH --> C[Checkpoint/Persistence]
  ORCH --> O[Observability]
  ORCH --> G[Approval Gate]
  G --> X[Controlled Execution]
```

## Domain workflow

ingest_architecture_proposal --> independent_domain_reviews --> identify_conflicts_and_missing_evidence --> cross_examination_round --> revise_domain_scores --> judge_against_decision_criteria --> produce_decision_conditions_and_dissent --> generate_review_record_and_adr_input

See `SKILL.md` for the implementation roadmap.

## Phase 1 implementation

The CLI validates the YAML configuration and typed domain input before constructing the provider-neutral workflow. Every stage appends evidence to a strict `RunState` and checkpoints through `RunStateRepository`; the CLI uses atomic local JSON files under `out/state/`, while tests use an in-memory repository. A run ID can resume without replaying completed stages, and changed input is rejected.

Structured JSON events capture run, stage, agent, provider/model, latency, usage, retry, status, and error-category fields. Known secret-bearing fields are recursively redacted, and raw input payloads are not logged. Local run IDs are validated before becoming paths.

Phase 1 remains deterministic and read-only. Domain specialists, real tool adapters, and vendor providers begin in later phases; see ADR-0002.
