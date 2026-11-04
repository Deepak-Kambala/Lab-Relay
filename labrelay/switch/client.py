"""Switch API Client for LabRelay.

Communicates with the local Switch Core instance over HTTP and WebSocket protocols.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import httpx

from labrelay.config import settings

logger = logging.getLogger(__name__)


class SwitchClient:
    """High-level client for the local Switch installation."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        admin_email: Optional[str] = None,
        admin_password: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.switch_api_url).rstrip("/")
        self.admin_email = admin_email or settings.switch_gateway_admin_email
        self.admin_password = admin_password or settings.switch_gateway_admin_password
        self._session_cookies: Dict[str, str] = {}
        self._cached_agents: Dict[str, Dict[str, Any]] = {}

    async def authenticate(self) -> Dict[str, str]:
        """Authenticate with Switch Gateway API to obtain session cookies."""
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            resp = await client.post(
                "/gateway/auth/login",
                json={
                    "email": self.admin_email,
                    "password": self.admin_password,
                },
            )
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Failed to authenticate with Switch Gateway: {resp.status_code} - {resp.text}"
                )
            self._session_cookies = dict(resp.cookies)
            logger.info("Successfully authenticated with Switch Gateway")
            return self._session_cookies

    async def _ensure_auth(self) -> Dict[str, str]:
        if not self._session_cookies:
            await self.authenticate()
        return self._session_cookies

    async def register_agent(
        self,
        name: str,
        display_name: str,
        description: str,
        overwrite: bool = True,
    ) -> Dict[str, Any]:
        """Register an agent in Switch and return its ID and API key."""
        cookies = await self._ensure_auth()
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            resp = await client.post(
                "/gateway/agents/register-other",
                json={
                    "name": name,
                    "display_name": display_name,
                    "description": description,
                    "overwrite": overwrite,
                },
                cookies=cookies,
            )
            if resp.status_code not in (200, 201):
                raise RuntimeError(
                    f"Failed to register agent '{name}' in Switch: {resp.status_code} - {resp.text}"
                )
            data = resp.json()
            self._cached_agents[name] = data
            logger.info("Registered Switch agent '%s' (ID: %s)", name, data.get("id"))
            return data

    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents in Switch."""
        cookies = await self._ensure_auth()
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            resp = await client.get("/gateway/agents", cookies=cookies)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to list agents: {resp.status_code} - {resp.text}")
            return resp.json()

    async def create_chat_room(
        self,
        name: str,
        agent_ids: List[str],
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a multi-agent collaboration room in Switch."""
        cookies = await self._ensure_auth()
        req_id = request_id or str(uuid.uuid4())
        payload = {
            "name": name,
            "agentIds": agent_ids,
            "requestId": req_id,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            resp = await client.post("/gateway/chats", json=payload, cookies=cookies)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Failed to create chat room in Switch: {resp.status_code} - {resp.text}"
                )
            data = resp.json()
            chat = data.get("chat", {})
            room_id = chat.get("roomId")
            logger.info("Created Switch collaboration room '%s' (ID: %s)", name, room_id)
            return chat

    async def post_user_message(
        self,
        room_id: str,
        body: str,
        mention_agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Post a user message into the Switch collaboration room."""
        cookies = await self._ensure_auth()
        req_id = request_id or str(uuid.uuid4())
        payload = {
            "body": body,
            "requestId": req_id,
            "mentionAgentId": mention_agent_id,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
            resp = await client.post(
                f"/gateway/chats/{room_id}/messages",
                json=payload,
                cookies=cookies,
            )
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Failed to post user message in room {room_id}: {resp.status_code} - {resp.text}"
                )
            return resp.json()

    async def get_room_messages(self, room_id: str) -> List[Dict[str, Any]]:
        """Retrieve all messages from a Switch collaboration room."""
        cookies = await self._ensure_auth()
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            resp = await client.get(f"/gateway/chats/{room_id}/messages", cookies=cookies)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch messages for room {room_id}: {resp.status_code} - {resp.text}"
                )
            return resp.json().get("messages", [])

    async def execute_agent_operation(
        self,
        agent_id: str,
        api_key: str,
        room_id: str,
        operation: str,
        arguments: Dict[str, Any],
        connection_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute an operation as a specific agent within a Switch room.

        Opens a transient WebSocket connection session if needed to establish agent presence.
        """
        conn_id = connection_id or str(uuid.uuid4())
        ws_url = (
            f"{self.base_url.replace('http://', 'ws://').replace('https://', 'wss://')}"
            f"/agents/{agent_id}/connection/ws?connection_id={conn_id}&rooms={room_id}"
        )
        headers = {"Authorization": f"Bearer {api_key}"}

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url, headers=headers) as ws:
                op_headers = {
                    "Authorization": f"Bearer {api_key}",
                    "X-Switch-Connection-Id": conn_id,
                }
                async with httpx.AsyncClient(base_url=self.base_url, timeout=20.0) as http_client:
                    # 1. Connect agent to room
                    r_conn = await http_client.post(
                        f"/agents/{agent_id}/ops/connect_to_room",
                        json={"room_id": room_id},
                        headers=op_headers,
                    )
                    if r_conn.status_code != 200:
                        logger.warning(
                            "Agent %s connect_to_room status %s: %s",
                            agent_id,
                            r_conn.status_code,
                            r_conn.text,
                        )

                    # 2. Call target operation
                    resp = await http_client.post(
                        f"/agents/{agent_id}/ops/{operation}",
                        json=arguments,
                        headers=op_headers,
                    )
                    if resp.status_code != 200:
                        raise RuntimeError(
                            f"Agent operation '{operation}' failed: {resp.status_code} - {resp.text}"
                        )
                    return resp.json().get("result", {})

