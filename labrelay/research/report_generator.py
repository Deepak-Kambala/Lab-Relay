"""Research Report Generator for LabRelay.

Generates rigorous, peer-reviewed structured research reports in Markdown and PDF formats.
Enforces the 12 required research sections and preserves verifiable literature references.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from fpdf import FPDF

from labrelay.config import settings
from labrelay.research.academic_sources import AcademicPaper
from labrelay.research.experiment_runner import ExperimentResult

logger = logging.getLogger(__name__)


@dataclass
class ResearchReportData:
    workflow_id: str
    question: str
    background: str
    related_work: str
    existing_approaches: str
    identified_limitations: str
    potential_research_gap: str
    proposed_hypothesis: str
    experiment_design: str
    baselines_and_metrics: str
    results: str
    threats_to_validity: str
    references: List[AcademicPaper]
    generated_at: str
    agent_contributions: Dict[str, str]


def _clean_pdf_text(text: str) -> str:
    """Normalize unicode characters for standard PDF fonts."""
    replacements = {
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "*",
        "…": "...",
        "≥": ">=",
        "≤": "<=",
        "²": "^2",
        "³": "^3",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")


class PDFReport(FPDF):
    """Custom FPDF class with academic styling, header, and page numbering."""

    def __init__(self, title: str):
        super().__init__()
        self.doc_title = title
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, _clean_pdf_text("LabRelay - Multi-Agent Academic Research Workspace"), border=0, align="L")
        self.ln(4)
        self.line(10, 16, 200, 16)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        page_str = f"Page {self.page_no()}/{{nb}}"
        self.cell(0, 10, page_str, border=0, align="C")


class ReportGenerator:
    """Generates Markdown and PDF versions of the LabRelay research report."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.reports_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "markdown").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "pdf").mkdir(parents=True, exist_ok=True)

    def generate_markdown(self, data: ResearchReportData) -> Path:
        """Render the 12 required sections into a clean Markdown report."""
        filename = f"report_{data.workflow_id}.md"
        path = self.output_dir / "markdown" / filename

        ref_lines = []
        for i, ref in enumerate(data.references, 1):
            ref_lines.append(f"{i}. {ref.format_citation()}")
        references_text = "\n".join(ref_lines) if ref_lines else "No external references cited."

        agents_text = "\n".join(
            f"- **{agent}**: {summary}" for agent, summary in data.agent_contributions.items()
        )

        content = f"""# LabRelay Research Assessment Report
**Workflow ID:** `{data.workflow_id}`  
**Generated At:** {data.generated_at}  
**Collaboration Infrastructure:** SandboxAQ Switch (Local Native Server)  

---

## Agent Collaboration Team
{agents_text}

---

## 1. Research Question
{data.question}

## 2. Problem Background
{data.background}

## 3. Related Work
{data.related_work}

## 4. Existing Approaches
{data.existing_approaches}

## 5. Identified Limitations
{data.identified_limitations}

## 6. Potential Research Gap
{data.potential_research_gap}

## 7. Proposed Hypothesis
{data.proposed_hypothesis}

## 8. Experiment Design
{data.experiment_design}

## 9. Baselines and Evaluation Metrics
{data.baselines_and_metrics}

## 10. Experimental Results
{data.results}

## 11. Limitations and Threats to Validity
{data.threats_to_validity}

## 12. References
{references_text}

---
*Report synthesized autonomously by LabRelay Multi-Agent Team (Scout, Skeptic, Experimenter, Reviewer) on Switch.*
"""
        path.write_text(content, encoding="utf-8")
        logger.info("Saved Markdown report to %s", path)
        return path

    def generate_pdf(self, data: ResearchReportData) -> Path:
        """Render the 12 required sections into a formal PDF report."""
        filename = f"report_{data.workflow_id}.pdf"
        path = self.output_dir / "pdf" / filename

        pdf = PDFReport(title="LabRelay Research Report")
        pdf.alias_nb_pages()
        pdf.add_page()

        # Document Header Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(20, 30, 55)
        pdf.cell(0, 10, "LabRelay Research Assessment", new_x="LMARGIN", new_y="NEXT", align="L")

        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(
            0,
            6,
            f"Workflow ID: {data.workflow_id} | Date: {data.generated_at} | Engine: Switch Multi-Agent",
            new_x="LMARGIN",
            new_y="NEXT",
            align="L",
        )
        pdf.ln(4)

        sections = [
            ("1. Research Question", data.question),
            ("2. Problem Background", data.background),
            ("3. Related Work", data.related_work),
            ("4. Existing Approaches", data.existing_approaches),
            ("5. Identified Limitations", data.identified_limitations),
            ("6. Potential Research Gap", data.potential_research_gap),
            ("7. Proposed Hypothesis", data.proposed_hypothesis),
            ("8. Experiment Design", data.experiment_design),
            ("9. Baselines & Evaluation Metrics", data.baselines_and_metrics),
            ("10. Experimental Results", data.results),
            ("11. Limitations & Threats to Validity", data.threats_to_validity),
        ]

        for title, text in sections:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 50, 90)
            pdf.cell(0, 8, _clean_pdf_text(title), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            clean_text = _clean_pdf_text(text)
            pdf.multi_cell(0, 5.5, clean_text)
            pdf.ln(3)

        # 12. References
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 50, 90)
        pdf.cell(0, 8, "12. References", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(40, 40, 40)

        if data.references:
            for i, ref in enumerate(data.references, 1):
                ref_text = f"[{i}] {ref.format_citation()}"
                clean_ref = _clean_pdf_text(ref_text.replace("**", "").replace("*", ""))
                pdf.multi_cell(0, 5, clean_ref)
                pdf.ln(1)
        else:
            pdf.cell(0, 6, "No external references.", new_x="LMARGIN", new_y="NEXT")

        pdf.output(str(path))
        logger.info("Saved PDF report to %s", path)
        return path
