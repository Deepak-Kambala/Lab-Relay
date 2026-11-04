import pytest
from pathlib import Path
from labrelay.research.academic_sources import AcademicPaper
from labrelay.research.report_generator import ReportGenerator, ResearchReportData


def test_report_generation(tmp_path: Path):
    generator = ReportGenerator(output_dir=tmp_path)
    paper = AcademicPaper(
        title="Clustering High-Dimensional Data",
        authors=["Alice Smith", "Bob Jones"],
        year=2023,
        doi="https://doi.org/10.1234/test",
        url="https://doi.org/10.1234/test",
        venue="ACM Computing Surveys",
        abstract="Analysis of clustering...",
        citation_count=10,
        source_api="OpenAlex",
    )
    data = ResearchReportData(
        workflow_id="wf-test-99",
        question="Can clustering algorithms identify structures in high-dimensional datasets?",
        background="Curse of dimensionality poses challenges...",
        related_work="Prior studies showed medoid stability...",
        existing_approaches="K-Means, PAM, Hierarchical...",
        identified_limitations="K-Means fails on non-spherical clusters...",
        potential_research_gap="Lack of medoid drift quantification in high-D...",
        proposed_hypothesis="H1: PAM outperforms K-Means under distance concentration...",
        experiment_design="Synthetic data with 50D and 300 samples...",
        baselines_and_metrics="WCSS, Runtime, Silhouette...",
        results="K-Means WCSS=14818.68, PAM WCSS=14818.68...",
        threats_to_validity="Synthetic Gaussian models may differ from biological data...",
        references=[paper],
        generated_at="2026-11-04 07:00:00 UTC",
        agent_contributions={"Scout": "Found papers", "Skeptic": "Critiqued"},
    )

    md_file = generator.generate_markdown(data)
    assert md_file.exists()
    content = md_file.read_text(encoding="utf-8")
    assert "1. Research Question" in content
    assert "12. References" in content
    assert "Alice Smith, Bob Jones" in content

    pdf_file = generator.generate_pdf(data)
    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 1000

