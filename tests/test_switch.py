import pytest
from labrelay.config import settings
from labrelay.switch.client import SwitchClient
from labrelay.switch.agents import AgentTeamManager


@pytest.mark.asyncio
async def test_switch_gateway_health_and_auth():
    client = SwitchClient(base_url=settings.switch_api_url)
    cookies = await client.authenticate()
    assert "switch_auth" in cookies
    
    agents = await client.list_agents()
    assert isinstance(agents, list)
    assert len(agents) >= 1


@pytest.mark.asyncio
async def test_switch_agent_team_registration():
    client = SwitchClient(base_url=settings.switch_api_url)
    team = AgentTeamManager(client=client)
    records = await team.ensure_agents_registered()
    
    assert "research-scout" in records
    assert "research-skeptic" in records
    assert "research-experimenter" in records
    assert "research-reviewer" in records
    
    for name, r in records.items():
        assert "id" in r
        assert "api_key" in r

