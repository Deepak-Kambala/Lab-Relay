"""Local LLM synthesis client utilizing Antigravity CLI (agy)."""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """Invokes the local authenticated agy engine to generate dynamic agent synthesis."""

    def __init__(self, agy_path: Optional[str] = None):
        self.agy_path = agy_path or os.environ.get("ANTIGRAVITY_AGENTAPI_EXE", "/Users/deepakkambala/.gemini/bin/agy")
        if not os.path.exists(self.agy_path):
            found = shutil.which("agy")
            if found:
                self.agy_path = found

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, timeout: float = 60.0) -> str:
        """Call agy --print to generate text response."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System Instructions:\n{system_prompt}\n\nTask:\n{prompt}"

        try:
            process = await asyncio.create_subprocess_exec(
                self.agy_path,
                "--print",
                full_prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            if process.returncode == 0:
                output = stdout_bytes.decode("utf-8", errors="replace").strip()
                if output:
                    return output
            
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            logger.warning("agy exited with %s: %s", process.returncode, stderr)
            return ""
        except asyncio.TimeoutError:
            logger.warning("agy generation timed out after %ss", timeout)
            return ""
        except Exception as e:
            logger.error("Failed to run agy: %s", e)
            return ""

