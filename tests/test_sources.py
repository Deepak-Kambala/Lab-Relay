import pytest
from labrelay.research.academic_sources import AcademicPaper, AcademicSourceProvider


def test_academic_paper_citation_format():
    paper = AcademicPaper(
        title="Fast and Eager k-Medoids Clustering",
        authors=["Erich Schubert", "Peter J. Rousseeuw"],
        year=2021,
        doi="https://doi.org/10.1016/j.is.2021.101804",
        url="https://doi.org/10.1016/j.is.2021.101804",
        venue="Information Systems",
        abstract="PAM improvement...",
        citation_count=42,
        source_api="OpenAlex",
    )
    citation = paper.format_citation()
    assert "Erich Schubert, Peter J. Rousseeuw" in citation
    assert "(2021)" in citation
    assert "Fast and Eager k-Medoids Clustering" in citation
    assert "https://doi.org/10.1016/j.is.2021.101804" in citation


@pytest.mark.asyncio
async def test_openalex_live_search():
    provider = AcademicSourceProvider()
    results = await provider.search("K-Means high dimensional clustering", limit=2)
    assert len(results) >= 1
    p = results[0]
    assert p.title
    assert p.year is not None or p.doi is not None
    assert p.source_api in ("OpenAlex", "SemanticScholar")

