"""Telegram Bot Application for LabRelay."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
import uuid
from typing import Dict, Optional

from telegram import InputFile, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from labrelay.config import settings
from labrelay.telegram.formatters import (
    format_help_message,
    format_status_message,
    format_summary_card,
    format_welcome_message,
)
from labrelay.workflow.models import ResearchWorkflow, WorkflowStage
from labrelay.workflow.runner import WorkflowRunner

logger = logging.getLogger(__name__)


class LabRelayTelegramBot:
    """Manages Telegram bot interactions and dispatches research workflows."""

    def __init__(self, runner: WorkflowRunner, token: Optional[str] = None):
        self.runner = runner
        self.token = token or settings.telegram_bot_token
        self.application: Optional[Application] = None
        # Track latest workflow per user
        self.user_latest_workflow: Dict[int, str] = {}
        # Active asyncio tasks per user
        self.user_tasks: Dict[int, asyncio.Task] = {}

    def _check_access(self, update: Update) -> bool:
        user = update.effective_user
        if not user:
            return False
        return settings.is_user_allowed(user_id=user.id, username=user.username)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /start."""
        if not self._check_access(update):
            await update.message.reply_text("⛔ Access denied. Your Telegram user is not authorized.")
            return
        await update.message.reply_text(
            format_welcome_message(),
            parse_mode=ParseMode.HTML,
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /help."""
        if not self._check_access(update):
            return
        await update.message.reply_text(
            format_help_message(),
            parse_mode=ParseMode.HTML,
        )

    async def research_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /research <question>."""
        if not self._check_access(update):
            await update.message.reply_text("⛔ Access denied.")
            return

        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        # Extract research question
        args = context.args
        if not args:
            await update.message.reply_text(
                "⚠️ Please provide a research question.\n"
                "Example: <code>/research Compare K-Means, PAM, and hierarchical clustering in high-dimensional scientific datasets.</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        question = " ".join(args).strip()
        workflow_id = f"lab-{uuid.uuid4().hex[:8]}"

        # Check if an existing workflow is already running for this user
        existing_task = self.user_tasks.get(user_id)
        if existing_task and not existing_task.done():
            await update.message.reply_text(
                "⏳ You already have an active research workflow running. Use /status or /cancel first.",
                parse_mode=ParseMode.HTML,
            )
            return

        workflow = ResearchWorkflow(
            workflow_id=workflow_id,
            user_id=user_id,
            chat_id=chat_id,
            question=question,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.user_latest_workflow[user_id] = workflow_id

        # Send initial acknowledgment
        ack_msg = await update.message.reply_text(
            f"🔬 <b>LabRelay Research Task Initialized</b>\n\n"
            f"<b>Workflow ID:</b> <code>{workflow_id}</code>\n"
            f"<b>Topic:</b> {question}\n\n"
            f"<i>Connecting to Switch multi-agent collaboration room...</i>",
            parse_mode=ParseMode.HTML,
        )

        # Progress callback to send meaningful updates to Telegram
        last_notified_text = ""

        async def on_progress(wf: ResearchWorkflow, update_text: str):
            nonlocal last_notified_text
            if update_text == last_notified_text:
                return
            last_notified_text = update_text
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"[{wf.workflow_id}] {update_text}",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception as e:
                logger.warning("Could not send progress update to Telegram: %s", e)

        # Launch workflow asynchronously
        async def run_task():
            try:
                completed_wf = await self.runner.execute_workflow(workflow, progress_callback=on_progress)
                if completed_wf.stage == WorkflowStage.COMPLETED:
                    # Send summary card
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=format_summary_card(completed_wf),
                        parse_mode=ParseMode.HTML,
                    )
                    # Send document files (Markdown & PDF)
                    if completed_wf.markdown_path and completed_wf.markdown_path.exists():
                        with open(completed_wf.markdown_path, "rb") as f:
                            await context.bot.send_document(
                                chat_id=chat_id,
                                document=f,
                                filename=completed_wf.markdown_path.name,
                                caption="📄 Markdown Research Report",
                            )
                    if completed_wf.pdf_path and completed_wf.pdf_path.exists():
                        with open(completed_wf.pdf_path, "rb") as f:
                            await context.bot.send_document(
                                chat_id=chat_id,
                                document=f,
                                filename=completed_wf.pdf_path.name,
                                caption="📑 PDF Formal Assessment Report",
                            )
            except Exception as ex:
                logger.exception("Error in background research task: %s", ex)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Workflow failed: {ex}",
                )

        task = asyncio.create_task(run_task())
        self.user_tasks[user_id] = task

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /status."""
        if not self._check_access(update):
            return

        user_id = update.effective_user.id
        wf_id = self.user_latest_workflow.get(user_id)
        workflow = self.runner.get_workflow(wf_id) if wf_id else None

        await update.message.reply_text(
            format_status_message(workflow),
            parse_mode=ParseMode.HTML,
        )

    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /report."""
        if not self._check_access(update):
            return

        user_id = update.effective_user.id
        wf_id = self.user_latest_workflow.get(user_id)
        workflow = self.runner.get_workflow(wf_id) if wf_id else None

        if not workflow or workflow.stage != WorkflowStage.COMPLETED:
            await update.message.reply_text(
                "ℹ️ No completed report available yet. Start a research task with <code>/research &lt;question&gt;</code>.",
                parse_mode=ParseMode.HTML,
            )
            return

        await update.message.reply_text(
            format_summary_card(workflow),
            parse_mode=ParseMode.HTML,
        )
        if workflow.markdown_path and workflow.markdown_path.exists():
            with open(workflow.markdown_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=workflow.markdown_path.name,
                    caption="📄 Markdown Research Report",
                )
        if workflow.pdf_path and workflow.pdf_path.exists():
            with open(workflow.pdf_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=workflow.pdf_path.name,
                    caption="📑 PDF Formal Assessment Report",
                )

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /cancel."""
        if not self._check_access(update):
            return

        user_id = update.effective_user.id
        wf_id = self.user_latest_workflow.get(user_id)
        task = self.user_tasks.get(user_id)

        if wf_id and self.runner.cancel_workflow(wf_id):
            if task and not task.done():
                task.cancel()
            await update.message.reply_text(
                f"🛑 Successfully cancelled workflow <code>{wf_id}</code>.",
                parse_mode=ParseMode.HTML,
            )
        else:
            await update.message.reply_text("ℹ️ No active workflow to cancel.")

    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for /reset."""
        if not self._check_access(update):
            return

        user_id = update.effective_user.id
        self.user_latest_workflow.pop(user_id, None)
        task = self.user_tasks.pop(user_id, None)
        if task and not task.done():
            task.cancel()

        await update.message.reply_text(
            "🔄 Conversation state reset. Send <code>/research &lt;question&gt;</code> to start fresh.",
            parse_mode=ParseMode.HTML,
        )

    def build_application(self) -> Application:
        """Construct the telegram bot Application instance."""
        builder = ApplicationBuilder().token(self.token)
        app = builder.build()

        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("research", self.research_command))
        app.add_handler(CommandHandler("status", self.status_command))
        app.add_handler(CommandHandler("report", self.report_command))
        app.add_handler(CommandHandler("cancel", self.cancel_command))
        app.add_handler(CommandHandler("reset", self.reset_command))

        self.application = app
        return app

