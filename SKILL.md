# SKILL.md — Multi-Agent Architecture Review Board

    ## 1. Mission

    Simulate an enterprise architecture review board with independent domain reviewers and an evidence-based adjudication process that avoids false consensus and makes dissent visible.

    ## 2. Product objective

    Build this repository into a portfolio-quality, production-oriented reference implementation that can run locally in WSL/macOS, in Docker, and later on Kubernetes. It must support multiple LLM providers through a stable abstraction and must remain usable in deterministic/mock mode for tests and demonstrations.

    ## 3. Required inputs

    - Architecture proposal and diagrams
- Requirements and NFRs
- Enterprise standards and guardrails
- Cost constraints
- Security, governance and operational requirements

    ## 4. Required outputs

    - APPROVE / APPROVE_WITH_CONDITIONS / REJECT / DEFER decision
- Independent reviewer findings
- Dissenting opinions
- Required conditions and evidence
- Weighted decision score
- Risk register
- ADR-ready rationale

    Outputs must be available as structured JSON. Human-readable Markdown reports may be generated from the same typed result models.

    ## 5. Agent topology

    Implement the following specialized agents as independently testable components:

    - `data_reviewer`
- `security_reviewer`
- `reliability_reviewer`
- `platform_reviewer`
- `finops_reviewer`
- `operability_reviewer`
- `ai_reviewer`
- `board_judge`

    The orchestrator owns workflow state. Specialist agents do not call one another directly unless an ADR explicitly introduces peer-to-peer coordination.

    ## 6. Tool/adaptor topology

    Create typed, least-privilege adapters for:

    - `proposal_loader`
- `standards_loader`
- `evidence_registry`
- `risk_scorer`
- `adr_writer`

    Rules:
    - Read operations and write operations must be separate methods.
    - Mutating tools must expose dry-run support when technically possible.
    - All mutations must return an audit payload.
    - Tool failures must be represented as typed errors; do not hide them inside model prose.
    - Add fake/in-memory adapters for tests before real integrations.

    ## 7. Canonical workflow

    Implement these stages as explicit workflow nodes:

    - 1. `ingest_architecture_proposal`
- 2. `independent_domain_reviews`
- 3. `identify_conflicts_and_missing_evidence`
- 4. `cross_examination_round`
- 5. `revise_domain_scores`
- 6. `judge_against_decision_criteria`
- 7. `produce_decision_conditions_and_dissent`
- 8. `generate_review_record_and_adr_input`

    Each node receives a typed workflow state and appends evidence/results without deleting prior evidence. Support resumability by serializing state after every stage.

    ## 8. Provider architecture

    Maintain a provider-neutral interface in `src/architecture_review_board/providers/base.py`.

    Required capabilities:
    - `generate_text`
    - `generate_structured`
    - `critique`
    - optional tool-call planning
    - token/usage metadata
    - timeout and retry configuration

    Add providers incrementally in this order:
    1. Mock provider (already scaffolded)
    2. OpenAI
    3. Anthropic
    4. Google Gemini
    5. AWS Bedrock
    6. Azure OpenAI
    7. Ollama/local models

    Vendor SDK types must not leak into domain models. Use environment variables and secret stores for credentials.

    ## 9. Reasoning and evidence contract

    Do not persist or expose hidden chain-of-thought. Persist concise decision evidence instead:
    - facts observed
    - evidence references
    - assumptions
    - hypotheses
    - alternatives considered
    - scores
    - final rationale
    - confidence and uncertainty

    Every high-impact recommendation must have a machine-readable evidence list.

    ## 10. Risk and safety model

    Implement a common `RiskAssessment` model with:
    - severity: LOW | MEDIUM | HIGH | CRITICAL
    - probability: 0.0-1.0
    - impact areas
    - mitigations
    - residual risk
    - approval_required
    - confidence

    Default to read-only/dry-run. Production writes require:
    - allow-listed tool
    - explicit environment
    - change identifier
    - approval token or approval callback
    - preconditions
    - postconditions
    - rollback instructions
    - audit event

    ## 11. Observability

    Add structured logging and OpenTelemetry-compatible hooks. Capture:
    - run_id
    - stage
    - agent
    - tool
    - latency
    - provider/model
    - input/output token usage when available
    - cost estimate when available
    - retry count
    - status
    - error category

    Never log secrets or raw sensitive payloads by default.

    ## 12. Configuration

    Keep configuration in YAML plus environment overrides. Required top-level sections:
    - `app`
    - `provider`
    - `workflow`
    - `risk`
    - `approval`
    - `observability`
    - `tools`

    Add schema validation and fail fast on invalid configuration.

    ## 13. CLI

    Extend the CLI with:
    - `run <input>`
    - `validate-config`
    - `show-config`
    - `eval`
    - `doctor`
    - `version`

    `run` must support `--dry-run`, `--provider`, `--config`, and `--output`.

    ## 14. API

    After the CLI is stable, add a FastAPI service:
    - `POST /runs`
    - `GET /runs/{run_id}`
    - `POST /runs/{run_id}/approve`
    - `POST /runs/{run_id}/cancel`
    - `GET /health`
    - `GET /ready`

    Long-running execution should use a pluggable queue/state backend, with an in-memory implementation for local development.

    ## 15. Persistence

    Introduce repository interfaces for:
    - workflow state
    - audit events
    - evidence
    - eval results
    - approvals

    Start with local JSON/SQLite, then add PostgreSQL. Keep persistence behind interfaces.

    ## 16. Evaluation strategy

    Build deterministic and model-based evals. Each case must contain:
    - input
    - expected required findings
    - forbidden findings/actions
    - expected risk range
    - evidence requirements

    Track:
    - correctness
    - groundedness/evidence coverage
    - false-positive rate
    - false-negative rate where applicable
    - action safety
    - latency
    - estimated model cost

    ## 17. Security requirements

    - No secrets in code, logs, fixtures or examples.
    - Use least-privilege identities for integrations.
    - Validate all file paths and external URLs.
    - Add prompt-injection-resistant boundaries when ingesting untrusted text.
    - Treat retrieved content as data, not executable instructions.
    - Add dependency and secret scanning in CI.
    - Pin production container base images by digest once the project matures.
    - Generate an SBOM in release workflows.
    - Run containers as non-root.

    ## 18. Deployment targets

    Support:
    - local Python
    - Docker / Docker Compose
    - Kubernetes
    - cloud container service later

    Terraform modules should be added only when a real deployment target is implemented; do not create fake infrastructure resources merely to populate the directory.

    ## 19. Implementation phases for Codex

    ### Phase 1 — Harden the core
    - Replace generic dictionaries with domain-specific Pydantic models.
    - Add config validation.
    - Add run-state persistence.
    - Add structured logging.
    - Expand unit tests to >80% coverage for core modules.

    ### Phase 2 — Implement domain agents
    - Implement each specialist listed in Section 5.
    - Give every specialist a typed input/output contract.
    - Add deterministic fixtures and unit tests.
    - Create critic/verifier behavior where appropriate.

    ### Phase 3 — Implement real tool adapters
    - Add one integration at a time.
    - Create read-only adapters first.
    - Use fixture-based integration tests.
    - Add retries, timeouts and typed failure handling.

    ### Phase 4 — Add real model providers
    - Implement provider adapters behind `BaseLLMProvider`.
    - Add structured-output validation and repair.
    - Add usage/cost telemetry.
    - Keep model/provider selection config-driven.

    ### Phase 5 — Evals and demo
    - Build at least 10 representative eval cases.
    - Create a scripted end-to-end demo.
    - Add a sample architecture diagram and screenshots/GIF only after the workflow is functional.
    - Publish benchmark results in `evals/README.md`.

    ### Phase 6 — Service and deployment
    - Add FastAPI.
    - Add persistence backend.
    - Harden Docker image.
    - Complete Kubernetes manifests.
    - Add release/security workflows.

    ## 20. Acceptance criteria

    - Reviewers produce independent first-pass reviews before seeing peer conclusions.
- Conflicts are surfaced rather than averaged away.
- The judge must explain why dissent was accepted or rejected.
- Approval with conditions produces machine-readable conditions.
- Missing material evidence can produce DEFER instead of hallucinated certainty.

    Additional global acceptance criteria:
    - `make test`, `make lint`, and `make demo` succeed.
    - The demo runs without any paid API key by using the mock provider.
    - New providers/tools can be added without modifying domain-agent contracts.
    - Every material architectural choice has an ADR.
    - README explains a 5-minute recruiter/interviewer demo path.

    ## 21. Codex working style

    When this skill is invoked:
    1. Inspect the repository before changing files.
    2. State the next implementation slice in the task output, not as a question.
    3. Implement the smallest vertical slice that produces a working/tested capability.
    4. Run tests/linters after modifications.
    5. Fix failures before stopping.
    6. Update docs and evals with the code.
    7. Do not replace working code with pseudocode.
    8. Do not claim an integration works unless it has been executed or clearly label it unverified.
    9. Prefer explicit TODOs tied to an implementation phase over speculative code.
    10. Leave the repository in a runnable state.
