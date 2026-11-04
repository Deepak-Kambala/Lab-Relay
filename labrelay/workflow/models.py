"""Workflow data models and state representations for LabRelay."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from labrelay.research.academic_sources import AcademicPaper
from labrelay.research.report_generator import ResearchReportData


class WorkflowStage(str, Enum):
    RECEIVED = "RECEIVED"
    SCOUTING = "SCOUTING"
    CRITICAL_REVIEW = "CRITICAL_REVIEW"
    EXPERIMENT_DESIGN = "EXPERIMENT_DESIGN"
    EXPERIMENT_EXECUTION = "EXPERIMENT_EXECUTION"
    FINAL_REVIEW = "FINAL_REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class StageRecord:
    stage: WorkflowStage
    agent_name: str
    started_at: str
    completed_at: Optional[str] = None
    input_summary: str = ""
    output_summary: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class ResearchWorkflow:
    workflow_id: str
    user_id: int
    chat_id: int
    question: str
    created_at: str
    stage: WorkflowStage = WorkflowStage.RECEIVED
    switch_room_id: Optional[str] = None
    records: List[StageRecord] = field(default_factory=list)
    papers: List[AcademicPaper] = field(default_factory=list)
    report_data: Optional[ResearchReportData] = None
    markdown_path: Optional[Path] = None
    pdf_path: Optional[Path] = None
    error: Optional[str] = None
    active_agent: Optional[str] = None

    def add_record(self, record: StageRecord) -> None:
        self.records.append(record)

    def current_status_summary(self) -> str:
        stage_names = {
            WorkflowStage.RECEIVED: " Request Received & Queued",
            WorkflowStage.SCOUTING: " Scouting Academic Literature (Scout)",
            WorkflowStage.CRITICAL_REVIEW: " Critical Academic Review (Skeptic)",
            WorkflowStage.EXPERIMENT_DESIGN: " Designing Experiments & Benchmarks (Experimenter)",
            WorkflowStage.EXPERIMENT_EXECUTION: " Running Empirical Validations (Experimenter)",
            WorkflowStage.FINAL_REVIEW: " Synthesizing Final Assessment (Reviewer)",
            WorkflowStage.COMPLETED: "Completed (Report Ready)",
            WorkflowStage.FAILED: "Workflow Error",
            WorkflowStage.CANCELLED: "Workflow Cancelled",
        }
        return stage_names.get(self.stage, str(self.stage))
