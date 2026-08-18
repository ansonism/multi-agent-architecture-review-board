# Multi-Agent Architecture Review Board

    A structured architecture-review system where specialized reviewers independently evaluate a proposal, challenge one another, and a judge produces a traceable decision with conditions and ADR-ready reasoning.

    ## Why this exists

    Simulate an enterprise architecture review board with independent domain reviewers and an evidence-based adjudication process that avoids false consensus and makes dissent visible.

    This repository is intentionally scaffolded as a **production-oriented agent project**, not a prompt-only demo. It starts with a deterministic mock provider so the complete orchestration path can be executed locally before adding any commercial LLM.

    ## Core workflow

    ingest_architecture_proposal -> independent_domain_reviews -> identify_conflicts_and_missing_evidence -> cross_examination_round -> revise_domain_scores -> judge_against_decision_criteria -> produce_decision_conditions_and_dissent -> generate_review_record_and_adr_input

    ## Specialized agents

    - `data_reviewer`
- `security_reviewer`
- `reliability_reviewer`
- `platform_reviewer`
- `finops_reviewer`
- `operability_reviewer`
- `ai_reviewer`
- `board_judge`

    ## Planned tool adapters

    - `proposal_loader`
- `standards_loader`
- `evidence_registry`
- `risk_scorer`
- `adr_writer`

    ## Quick start

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    multi-architecture-review-board run examples/sample_input.json --output out/result.json
    pytest
    ```

    Or:

    ```bash
    make setup
    make demo
    make test
    ```

    ## Safety defaults

    - Mock/dry-run behavior is the default.
    - External systems are accessed only through explicit adapters.
    - No production mutation should be added without an approval gate.
    - Facts, assumptions, hypotheses and recommendations should remain distinguishable in outputs.
    - Credentials must come from environment/secret stores, never source control.

    ## Codex implementation guide

    Start with [`SKILL.md`](./SKILL.md). It defines the mission, architecture, implementation sequence, acceptance criteria and guardrails Codex should follow.

    ## Repository layout

    ```text
    .
    ├── AGENTS.md
    ├── SKILL.md
    ├── config/
    ├── docs/
    ├── evals/
    ├── examples/
    ├── kubernetes/
    ├── prompts/
    ├── scripts/
    ├── src/architecture_review_board/
    ├── terraform/
    └── tests/
    ```

    ## Current state

    **Phase 1 core.** The typed harness validates configuration and domain inputs, writes an atomic checkpoint after every stage, supports idempotent resume by run ID, and emits redacted structured logs. The default CLI stores state under `out/state/`. `make demo`, `make test`, and `make lint` verify the runnable mock-provider implementation.