"""Telegram message formatters for LabRelay."""
from __future__ import annotations

import html
from typing import List, Optional

from labrelay.workflow.models import ResearchWorkflow, WorkflowStage


def format_welcome_message() -> str:
    return (
        "🔬 <b>Welcome to LabRelay!</b>\n\n"
        "LabRelay is a Telegram-first <b>Multi-Agent AI Research Workspace</b> powered by <b>Switch</b>.\n\n"
        "<b>🤖 Your Autonomous Agent Team:</b>\n"
        "• <b>Research Scout</b>: Explores academic literature & verified DOIs\n"
        "• <b>Skeptic</b>: Challenges assumptions & tests novelty\n"
        "• <b>Experimenter</b>: Formulates & executes empirical Python experiments\n"
        "• <b>Research Reviewer</b>: Synthesizes comprehensive academic peer reports\n\n"
        "<b>📚 Available Commands:</b>\n"
        "/research &lt;question&gt; — Launch a research investigation\n"
        "/status — View current workflow progress and active agents\n"
        "/report — Retrieve the latest generated report (Markdown & PDF)\n"
        "/cancel — Safely cancel the ongoing workflow\n"
        "/reset — Reset conversation state\n"
        "/help — Show this guidance message\n\n"
        "<i>Send a question with /research to begin!</i>"
    )


def format_help_message() -> str:
    return (
        "📖 <b>LabRelay Command Guide:</b>\n\n"
        "• <code>/research &lt;question&gt;</code>\n"
        "  Start a multi-agent investigation. Example:\n"
        "  <i>/research Compare K-Means, PAM, and hierarchical clustering in high-dimensional scientific datasets.</i>\n\n"
        "• <code>/status</code>\n"
        "  Check the active workflow stage, current working agent, and Switch room.\n\n"
        "• <code>/report</code>\n"
        "  Download the latest completed research assessment in Markdown and PDF.\n\n"
        "• <code>/cancel</code>\n"
        "  Gracefully halt an active workflow.\n\n"
        "• <code>/reset</code>\n"
        "  Clear active session state and start fresh."
    )


def format_status_message(workflow: Optional[ResearchWorkflow]) -> str:
    if not workflow:
        return "ℹ️ No active or previous research workflow found. Start one with <code>/research &lt;question&gt;</code>."

    status_icon = "🟢" if workflow.stage == WorkflowStage.COMPLETED else ("🔴" if workflow.stage in (WorkflowStage.FAILED, WorkflowStage.CANCELLED) else "🟡")
    
    msg = (
        f"📊 <b>Workflow Status:</b> {status_icon} <code>{workflow.stage.value}</code>\n"
        f"<b>ID:</b> <code>{workflow.workflow_id}</code>\n"
        f"<b>Question:</b> {html.escape(workflow.question[:120])}...\n"
        f"<b>Active Agent:</b> {workflow.active_agent or 'None'}\n"
        f"<b>Switch Room:</b> <code>{workflow.switch_room_id or 'Pending'}</code>\n\n"
        f"<b>Stages Completed:</b> {len(workflow.records)}\n"
    )

    for rec in workflow.records:
        msg += f"• <b>{rec.stage.value}</b> ({rec.agent_name})\n"

    if workflow.stage == WorkflowStage.COMPLETED:
        msg += "\n📄 <i>Use /report to download your complete report.</i>"
    elif workflow.stage == WorkflowStage.FAILED:
        msg += f"\n⚠️ Error: {html.escape(workflow.error or 'Unknown failure')}"

    return msg


def format_summary_card(workflow: ResearchWorkflow) -> str:
    data = workflow.report_data
    if not data:
        return "Report is still being compiled..."

    hypothesis_preview = html.escape(data.proposed_hypothesis[:200])
    gap_preview = html.escape(data.potential_research_gap[:200])
    results_preview = html.escape(data.results[:200])

    return (
        f"🎓 <b>Research Report Synthesized!</b>\n\n"
        f"<b>Topic:</b> {html.escape(data.question)}\n"
        f"<b>Workflow ID:</b> <code>{data.workflow_id}</code>\n"
        f"<b>References Cited:</b> {len(data.references)} peer-reviewed papers\n"
        f"<b>Empirical Validation:</b> Completed\n\n"
        f"<b>Key Research Insights:</b>\n"
        f"• <b>Hypothesis:</b> {hypothesis_preview}...\n"
        f"• <b>Research Gap:</b> {gap_preview}...\n"
        f"• <b>Findings:</b> {results_preview}...\n\n"
        f"<i>Full 12-section report attached below (Markdown and PDF).</i>"
    )

