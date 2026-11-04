"""Agent team specifications and coordination for LabRelay in Switch."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from labrelay.switch.client import SwitchClient


@dataclass
class AgentSpec:
    name: str
    display_name: str
    role_title: str
    description: str
    system_prompt: str


AGENT_SPECS: Dict[str, AgentSpec] = {
    "research-scout": AgentSpec(
        name="research-scout",
        display_name="Research Scout",
        role_title="Academic Literature Explorer",
        description="Explores peer-reviewed academic literature, identifies existing methods, state-of-the-art baselines, and research gaps without fabrication.",
        system_prompt=(
            "You are the Research Scout for LabRelay. Your task is to investigate the user's research question, "
            "synthesize real peer-reviewed literature, identify existing methods, benchmark datasets, and pin down genuine research gaps. "
            "Never fabricate citations, DOIs, or author names. Always anchor findings in verifiable academic literature."
        ),
    ),
    "research-skeptic": AgentSpec(
        name="research-skeptic",
        display_name="Skeptic",
        role_title="Critical Academic Evaluator",
        description="Critically challenges assumptions, tests methodological rigor, questions novelty claims, and identifies threats to validity.",
        system_prompt=(
            "You are the Skeptic for LabRelay. Your role is rigorous, constructive academic criticism. "
            "Challenge every claim made by the Scout: Are the assumptions warranted? Is the novelty genuine or superficial? "
            "What are the curse-of-dimensionality pitfalls, computational complexity bounds, or evaluation biases?"
        ),
    ),
    "research-experimenter": AgentSpec(
        name="research-experimenter",
        display_name="Experimenter",
        role_title="Empirical Validation Engineer",
        description="Designs reproducible experiments, selects datasets and baselines, implements Python test scripts, and reports actual results.",
        system_prompt=(
            "You are the Experimenter for LabRelay. Your job is to translate the research question into an empirical benchmark. "
            "Propose concrete datasets, baseline algorithms, and evaluation metrics. Write and execute clean, safe Python experiments "
            "in the workspace, and report actual empirical outcomes separately from theoretical expectations."
        ),
    ),
    "research-reviewer": AgentSpec(
        name="research-reviewer",
        display_name="Research Reviewer",
        role_title="Senior Peer Reviewer",
        description="Conducts comprehensive peer review, assesses scientific validity, reproducibility, limitations, and synthesizes the final research report.",
        system_prompt=(
            "You are the Research Reviewer for LabRelay. Review the entire collaborative investigation as a critical academic reviewer. "
            "Synthesize the Scout's literature findings, the Skeptic's critiques, and the Experimenter's empirical results into a comprehensive, "
            "12-section research report with verifiable references, limitations, and future directions."
        ),
    ),
}


class AgentTeamManager:
    """Manages the lifecycle and credentials of the 4 LabRelay agents in Switch."""

    def __init__(self, client: SwitchClient):
        self.client = client
        self.agent_records: Dict[str, Dict[str, Any]] = {}

    async def ensure_agents_registered(self) -> Dict[str, Dict[str, Any]]:
        """Ensures all 4 agents exist in Switch and stores their IDs and API keys."""
        for name, spec in AGENT_SPECS.items():
            record = await self.client.register_agent(
                name=spec.name,
                display_name=spec.display_name,
                description=spec.description,
                overwrite=True,
            )
            self.agent_records[name] = record
        return self.agent_records

    def get_agent_id(self, name: str) -> Optional[str]:
        return self.agent_records.get(name, {}).get("id")

    def get_agent_api_key(self, name: str) -> Optional[str]:
        return self.agent_records.get(name, {}).get("api_key")

    def get_all_agent_ids(self) -> List[str]:
        return [r["id"] for r in self.agent_records.values() if "id" in r]

