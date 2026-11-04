"""State machine transitions and guard conditions for LabRelay workflows."""
from __future__ import annotations

import logging
from typing import Set

from labrelay.workflow.models import WorkflowStage

logger = logging.getLogger(__name__)


VALID_TRANSITIONS = {
    WorkflowStage.RECEIVED: {WorkflowStage.SCOUTING, WorkflowStage.CANCELLED, WorkflowStage.FAILED},
    WorkflowStage.SCOUTING: {WorkflowStage.CRITICAL_REVIEW, WorkflowStage.CANCELLED, WorkflowStage.FAILED},
    WorkflowStage.CRITICAL_REVIEW: {WorkflowStage.EXPERIMENT_DESIGN, WorkflowStage.FINAL_REVIEW, WorkflowStage.CANCELLED, WorkflowStage.FAILED},
    WorkflowStage.EXPERIMENT_DESIGN: {WorkflowStage.EXPERIMENT_EXECUTION, WorkflowStage.FINAL_REVIEW, WorkflowStage.CANCELLED, WorkflowStage.FAILED},
    WorkflowStage.EXPERIMENT_EXECUTION: {WorkflowStage.FINAL_REVIEW, WorkflowStage.CANCELLED, WorkflowStage.FAILED},
    WorkflowStage.FINAL_REVIEW: {WorkflowStage.COMPLETED, WorkflowStage.CANCELLED, WorkflowStage.FAILED},
    WorkflowStage.COMPLETED: set(),
    WorkflowStage.FAILED: set(),
    WorkflowStage.CANCELLED: set(),
}


class WorkflowStateMachine:
    """Validates and applies stage transitions on a research workflow."""

    @staticmethod
    def can_transition(current: WorkflowStage, target: WorkflowStage) -> bool:
        allowed = VALID_TRANSITIONS.get(current, set())
        return target in allowed

    @staticmethod
    def transition(current: WorkflowStage, target: WorkflowStage) -> WorkflowStage:
        if not WorkflowStateMachine.can_transition(current, target):
            raise ValueError(f"Illegal workflow transition: {current.value} -> {target.value}")
        logger.info("Workflow stage transition: %s -> %s", current.value, target.value)
        return target

