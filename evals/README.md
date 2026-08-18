# Evaluation plan

    Start with deterministic evals against the mock/fake adapters, then add provider-backed eval runs.

    Domain acceptance targets from `SKILL.md`:

    - Reviewers produce independent first-pass reviews before seeing peer conclusions.
- Conflicts are surfaced rather than averaged away.
- The judge must explain why dissent was accepted or rejected.
- Approval with conditions produces machine-readable conditions.
- Missing material evidence can produce DEFER instead of hallucinated certainty.

    Do not use an LLM judge as the sole source of truth for safety-critical or mechanically verifiable assertions.

Phase 1 eval cases are validated against the strict `EvalCase` contract. They declare required stages and findings, forbidden findings/actions, an expected risk range, and minimum evidence coverage. The suite runs deterministically with `MockProvider` and requires no network access or model judge.
