"""Academic Literature Source Integration for LabRelay.

Fetches verifiable papers, citations, and DOI links from OpenAlex and Semantic Scholar.
Never fabricates citations or novelty claims.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import List, Optional

import httpx

from labrelay.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AcademicPaper:
    title: str
    authors: List[str]
    year: Optional[int]
    doi: Optional[str]
    url: str
    venue: Optional[str]
    abstract: Optional[str]
    citation_count: int
    source_api: str

    def format_citation(self) -> str:
        """Format paper as an academic citation."""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += " et al."
        year_str = f"({self.year})" if self.year else "(n.d.)"
        venue_str = f" In *{self.venue}*." if self.venue else ""
        doi_str = f" DOI: {self.doi}" if self.doi else f" URL: {self.url}"
        return f"{authors_str} {year_str}. **{self.title}**.{venue_str}{doi_str}"


class AcademicSourceProvider:
    """Fetches real academic literature from OpenAlex with Semantic Scholar fallback."""

    def __init__(self, semantic_scholar_api_key: Optional[str] = None):
        self.ss_api_key = semantic_scholar_api_key or settings.semantic_scholar_api_key
        self.openalex_base = "https://api.openalex.org"
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1"

    async def search(self, query: str, limit: int = 5) -> List[AcademicPaper]:
        """Search academic literature using OpenAlex and Semantic Scholar."""
        papers: List[AcademicPaper] = []

        # 1. Primary: OpenAlex (reliable, open, comprehensive)
        try:
            openalex_papers = await self._search_openalex(query, limit=limit)
            papers.extend(openalex_papers)
            logger.info("Retrieved %d papers from OpenAlex for query '%s'", len(openalex_papers), query)
        except Exception as e:
            logger.warning("OpenAlex search failed: %s", e)

        # 2. Secondary: Semantic Scholar (if needed or to complement)
        if len(papers) < limit:
            try:
                ss_papers = await self._search_semantic_scholar(query, limit=limit - len(papers))
                # Deduplicate by title
                existing_titles = {p.title.lower() for p in papers}
                for p in ss_papers:
                    if p.title.lower() not in existing_titles:
                        papers.append(p)
                        existing_titles.add(p.title.lower())
                logger.info("Retrieved additional papers from Semantic Scholar (total: %d)", len(papers))
            except Exception as e:
                logger.warning("Semantic Scholar search fallback skipped: %s", e)

        return papers[:limit]

    async def _search_openalex(self, query: str, limit: int = 5) -> List[AcademicPaper]:
        params = {
            "search": query,
            "per-page": limit,
            "sort": "relevance_score:desc",
        }
        headers = {"User-Agent": "LabRelay-Research/1.0 (mailto:admin@switch.local)"}

        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(f"{self.openalex_base}/works", params=params, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAlex error: {resp.status_code} - {resp.text}")

            data = resp.json()
            results: List[AcademicPaper] = []
            for item in data.get("results", []):
                title = item.get("title") or "Untitled Publication"
                authors = []
                for a in item.get("authorships", []):
                    auth_obj = a.get("author") or {}
                    name = auth_obj.get("display_name")
                    if name:
                        authors.append(name)

                year = item.get("publication_year")
                doi = item.get("doi")
                url = doi or item.get("id") or "https://openalex.org"

                primary_loc = item.get("primary_location") or {}
                source_obj = primary_loc.get("source") or {}
                venue = source_obj.get("display_name")

                # Abstract inversion reconstruction if available
                abstract_inverted = item.get("abstract_inverted_index")
                abstract = None
                if abstract_inverted and isinstance(abstract_inverted, dict):
                    word_pos: List[tuple[int, str]] = []
                    for word, positions in abstract_inverted.items():
                        for pos in positions:
                            word_pos.append((pos, word))
                    word_pos.sort()
                    abstract = " ".join(w for _, w in word_pos[:100])
                    if len(word_pos) > 100:
                        abstract += "..."

                citation_count = item.get("cited_by_count", 0)

                results.append(
                    AcademicPaper(
                        title=title,
                        authors=authors if authors else ["Anonymous"],
                        year=year,
                        doi=doi,
                        url=url,
                        venue=venue,
                        abstract=abstract,
                        citation_count=citation_count,
                        source_api="OpenAlex",
                    )
                )
            return results

    async def _search_semantic_scholar(self, query: str, limit: int = 5) -> List[AcademicPaper]:
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,url,abstract,citationCount,venue",
        }
        headers = {"User-Agent": "LabRelay-Research/1.0"}
        if self.ss_api_key:
            headers["x-api-key"] = self.ss_api_key

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.semantic_scholar_base}/paper/search",
                params=params,
                headers=headers,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Semantic Scholar error: {resp.status_code}")

            data = resp.json()
            results: List[AcademicPaper] = []
            for item in data.get("data", []):
                title = item.get("title") or "Untitled Publication"
                authors = [
                    a.get("name", "")
                    for a in item.get("authors", [])
                    if a.get("name")
                ]
                year = item.get("year")
                url = item.get("url") or f"https://www.semanticscholar.org/paper/{item.get('paperId')}"
                abstract = item.get("abstract")
                venue = item.get("venue")
                citation_count = item.get("citationCount", 0)

                results.append(
                    AcademicPaper(
                        title=title,
                        authors=authors if authors else ["Anonymous"],
                        year=year,
                        doi=None,
                        url=url,
                        venue=venue,
                        abstract=abstract[:400] + "..." if abstract and len(abstract) > 400 else abstract,
                        citation_count=citation_count,
                        source_api="SemanticScholar",
                    )
                )
            return results
