"""Main application entry point for LabRelay."""
from __future__ import annotations

import asyncio
import logging
import signal
import sys
from typing import Optional

from labrelay.config import settings
from labrelay.research.academic_sources import AcademicSourceProvider
from labrelay.research.experiment_runner import ExperimentRunner
from labrelay.research.report_generator import ReportGenerator
from labrelay.switch.agents import AgentTeamManager
from labrelay.switch.client import SwitchClient
from labrelay.telegram.bot import LabRelayTelegramBot
from labrelay.workflow.runner import WorkflowRunner

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
)
logger = logging.getLogger("labrelay")


def create_app() -> LabRelayTelegramBot:
    """Wire together dependencies and build the Telegram bot application."""
    logger.info("Initializing LabRelay application...")
    logger.info("Switch Core Endpoint: %s", settings.switch_api_url)

    switch_client = SwitchClient(base_url=settings.switch_api_url)
    team_manager = AgentTeamManager(client=switch_client)
    source_provider = AcademicSourceProvider()
    experiment_runner = ExperimentRunner(workspace_dir=settings.workspace_dir)
    report_generator = ReportGenerator(output_dir=settings.reports_dir)

    workflow_runner = WorkflowRunner(
        switch_client=switch_client,
        team_manager=team_manager,
        source_provider=source_provider,
        experiment_runner=experiment_runner,
        report_generator=report_generator,
    )

    telegram_bot = LabRelayTelegramBot(
        runner=workflow_runner,
        token=settings.telegram_bot_token,
    )
    return telegram_bot


def main():
    """Run LabRelay Telegram Bot long-polling."""
    bot = create_app()
    app = bot.build_application()

    logger.info("Starting Telegram long polling for @%s...", settings.telegram_bot_username)
    print(f"\n=======================================================")
    print(f"🚀 LabRelay Multi-Agent Research Workspace is ACTIVE!")
    print(f"🤖 Telegram Bot: https://t.me/{settings.telegram_bot_username}")
    print(f"🔌 Switch Engine: {settings.switch_api_url}")
    print(f"=======================================================\n")

    app.run_polling(allowed_updates=["message", "edited_message", "callback_query"])


if __name__ == "__main__":
    main()

