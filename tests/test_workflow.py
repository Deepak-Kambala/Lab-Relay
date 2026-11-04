import pytest
from labrelay.workflow.models import ResearchWorkflow, WorkflowStage, StageRecord
from labrelay.workflow.state_machine import WorkflowStateMachine


def test_state_machine_valid_transitions():
    assert WorkflowStateMachine.can_transition(WorkflowStage.RECEIVED, WorkflowStage.SCOUTING)
    assert WorkflowStateMachine.can_transition(WorkflowStage.SCOUTING, WorkflowStage.CRITICAL_REVIEW)
    assert WorkflowStateMachine.can_transition(WorkflowStage.CRITICAL_REVIEW, WorkflowStage.EXPERIMENT_DESIGN)
    assert WorkflowStateMachine.can_transition(WorkflowStage.EXPERIMENT_DESIGN, WorkflowStage.EXPERIMENT_EXECUTION)
    assert WorkflowStateMachine.can_transition(WorkflowStage.EXPERIMENT_EXECUTION, WorkflowStage.FINAL_REVIEW)
    assert WorkflowStateMachine.can_transition(WorkflowStage.FINAL_REVIEW, WorkflowStage.COMPLETED)


def test_state_machine_invalid_transition():
    assert not WorkflowStateMachine.can_transition(WorkflowStage.RECEIVED, WorkflowStage.COMPLETED)
    assert not WorkflowStateMachine.can_transition(WorkflowStage.SCOUTING, WorkflowStage.EXPERIMENT_EXECUTION)
    
    with pytest.raises(ValueError):
        WorkflowStateMachine.transition(WorkflowStage.RECEIVED, WorkflowStage.COMPLETED)


def test_workflow_cancellation():
    assert WorkflowStateMachine.can_transition(WorkflowStage.SCOUTING, WorkflowStage.CANCELLED)
    assert WorkflowStateMachine.can_transition(WorkflowStage.CRITICAL_REVIEW, WorkflowStage.CANCELLED)
    assert WorkflowStateMachine.can_transition(WorkflowStage.EXPERIMENT_EXECUTION, WorkflowStage.CANCELLED)


def test_workflow_model():
    wf = ResearchWorkflow(
        workflow_id="test-123",
        user_id=12345,
        chat_id=67890,
        question="Test clustering high-dimensional data",
        created_at="2026-11-04T00:00:00Z",
    )
    assert wf.stage == WorkflowStage.RECEIVED
    wf.add_record(
        StageRecord(
            stage=WorkflowStage.SCOUTING,
            agent_name="research-scout",
            started_at="2026-11-04T00:01:00Z",
            output_summary="Found papers",
        )
    )
    assert len(wf.records) == 1
    assert "Received" in wf.current_status_summary()

