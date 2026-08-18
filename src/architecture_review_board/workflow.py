from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from time import perf_counter
from uuid import uuid4

from .models import (
    ArchitectureProposalInput,
    Evidence,
    ExecutionContext,
    RiskAssessment,
    RunState,
    RunStatus,
    Severity,
    StageResult,
    utc_now,
)
from .observability import log_event
from .persistence import InMemoryRunStateRepository, RunStateRepository
from .providers.base import BaseLLMProvider

DEFAULT_STAGES = [
    "ingest_architecture_proposal",
    "independent_domain_reviews",
    "identify_conflicts_and_missing_evidence",
    "cross_examination_round",
    "revise_domain_scores",
    "judge_against_decision_criteria",
    "produce_decision_conditions_and_dissent",
    "generate_review_record_and_adr_input",
]

STAGE_AGENTS = {stage: "board_orchestrator" for stage in DEFAULT_STAGES}


class Workflow:
    def __init__(
        self,
        provider: BaseLLMProvider,
        stages: list[str] | None = None,
        repository: RunStateRepository | None = None,
        *,
        checkpoint_each_stage: bool = True,
        clock: Callable[[], datetime] = utc_now,
        run_id_factory: Callable[[], str] = lambda: str(uuid4()),
    ) -> None:
        self.provider = provider
        self.stages = list(stages or DEFAULT_STAGES)
        self.repository = repository or InMemoryRunStateRepository()
        self.checkpoint_each_stage = checkpoint_each_stage
        self.clock = clock
        self.run_id_factory = run_id_factory

    def run(
        self,
        request: ArchitectureProposalInput,
        execution: ExecutionContext | None = None,
        *,
        run_id: str | None = None,
    ) -> RunState:
        effective_run_id = run_id or self.run_id_factory()
        state = self.repository.load(effective_run_id)
        if state is None:
            now = self.clock()
            state = RunState(
                run_id=effective_run_id,
                started_at=now,
                updated_at=now,
                request=request,
                execution=execution or ExecutionContext(),
            )
            self.repository.save(state)
        elif state.request != request:
            raise ValueError("Cannot resume a run with different request input")

        completed = {result.stage for result in state.stages}
        for index, stage in enumerate(self.stages, start=1):
            if stage in completed:
                continue
            started = perf_counter()
            agent = STAGE_AGENTS.get(stage, "request_commander")
            log_event(
                "stage_started",
                run_id=state.run_id,
                stage=stage,
                agent=agent,
                provider=state.execution.provider,
                status="RUNNING",
            )
            prompt = (
                f"Project: {state.project}\n"
                f"Case: {request.case_id}\n"
                f"Stage: {stage}\n"
                f"Evidence count: {len(request.evidence)}\n"
                "Produce concise, evidence-oriented analysis."
            )
            analysis = self.provider.generate_text(
                system="You are a deterministic development harness.", prompt=prompt
            )
            supplied_evidence = [
                Evidence(
                    source=item.type,
                    summary=item.summary,
                    reference=item.reference or item.id,
                )
                for item in request.evidence
            ]
            if not supplied_evidence:
                supplied_evidence = [
                    Evidence(
                        source="request_input",
                        summary=f"Stage {index} processed validated request input.",
                        reference=request.case_id,
                    )
                ]
            result = StageResult(
                stage=stage,
                agent=agent,
                summary=analysis,
                evidence=supplied_evidence,
                findings=[f"Mock-mode stage completed: {stage}"],
                assumptions=["No external-system state was queried in mock mode."],
                alternatives_considered=["Defer action until real adapters supply more evidence."],
                rationale="Validated input was processed without external mutation.",
                risk=RiskAssessment(
                    severity=Severity.LOW,
                    probability=0.1,
                    impact_areas=["development"],
                    mitigations=["Dry-run mode and provider-neutral mock execution."],
                    residual_risk="External conditions are not represented in mock mode.",
                    approval_required=False,
                    confidence=1.0,
                ),
                usage=self.provider.usage_metadata(),
                completed_at=self.clock(),
            )
            state.add_stage(result, updated_at=self.clock())
            if self.checkpoint_each_stage:
                self.repository.save(state)
            log_event(
                "stage_completed",
                run_id=state.run_id,
                stage=stage,
                agent=agent,
                latency_ms=round((perf_counter() - started) * 1000, 3),
                provider=result.usage.provider,
                model=result.usage.model,
                input_tokens=result.usage.input_tokens,
                output_tokens=result.usage.output_tokens,
                retry_count=result.usage.retry_count,
                status="COMPLETED",
                error_category=None,
            )

        state.status = RunStatus.COMPLETED
        state.updated_at = self.clock()
        self.repository.save(state)
        log_event("run_completed", run_id=state.run_id, status=state.status.value)
        return state
