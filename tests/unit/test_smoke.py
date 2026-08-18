from datetime import UTC, datetime

import pytest

from architecture_review_board.models import ArchitectureProposalInput, EvidenceInput, RunStatus
from architecture_review_board.persistence import InMemoryRunStateRepository
from architecture_review_board.providers.mock import MockProvider
from architecture_review_board.workflow import DEFAULT_STAGES, Workflow

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def request() -> ArchitectureProposalInput:
    return ArchitectureProposalInput(
        case_id="test-001",
        title="Pipeline delayed",
        description="The daily pipeline missed its expected completion time.",
        evidence=[EvidenceInput(id="ev-1", type="alert", summary="SLA missed")],
    )


def test_workflow_runs_all_stages_deterministically() -> None:
    state = Workflow(MockProvider(), clock=lambda: NOW, run_id_factory=lambda: "run-001").run(
        request()
    )

    assert state.status == RunStatus.COMPLETED
    assert state.run_id == "run-001"
    assert [stage.stage for stage in state.stages] == DEFAULT_STAGES
    assert all(stage.evidence for stage in state.stages)
    assert all(stage.usage.provider == "mock" for stage in state.stages)
    assert all(stage.completed_at == NOW for stage in state.stages)


def test_workflow_resumes_without_repeating_completed_stages() -> None:
    repository = InMemoryRunStateRepository()
    first = Workflow(
        MockProvider(),
        stages=DEFAULT_STAGES[:2],
        repository=repository,
        clock=lambda: NOW,
    ).run(request(), run_id="resume-001")
    assert len(first.stages) == 2

    resumed = Workflow(MockProvider(), repository=repository, clock=lambda: NOW).run(
        request(), run_id="resume-001"
    )
    assert len(resumed.stages) == len(DEFAULT_STAGES)
    assert len({stage.stage for stage in resumed.stages}) == len(DEFAULT_STAGES)


def test_workflow_rejects_changed_input_when_resuming() -> None:
    repository = InMemoryRunStateRepository()
    workflow = Workflow(MockProvider(), repository=repository)
    workflow.run(request(), run_id="resume-002")
    changed = request().model_copy(update={"title": "Different request"})

    with pytest.raises(ValueError, match="different request"):
        workflow.run(changed, run_id="resume-002")


def test_workflow_creates_fallback_evidence() -> None:
    no_evidence = request().model_copy(update={"evidence": []})
    state = Workflow(MockProvider(), stages=[DEFAULT_STAGES[0]]).run(no_evidence)
    assert state.stages[0].evidence[0].source == "request_input"
