"""Lightweight Web Dashboard for LabRelay.

Visualizes active research workflows, agent collaboration in Switch,
message history, and downloadable reports.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from labrelay.config import settings
from labrelay.workflow.runner import WorkflowRunner


def create_dashboard_app(runner: WorkflowRunner) -> FastAPI:
    app = FastAPI(title="LabRelay Web Dashboard")

    @app.get("/", response_class=HTMLResponse)
    async def dashboard_index():
        workflows = list(runner.active_workflows.values())
        rows_html = ""
        for wf in reversed(workflows):
            report_links = ""
            if wf.markdown_path and wf.markdown_path.exists():
                report_links += f'<a class="btn" href="/reports/md/{wf.workflow_id}" target="_blank">Markdown</a> '
            if wf.pdf_path and wf.pdf_path.exists():
                report_links += f'<a class="btn" href="/reports/pdf/{wf.workflow_id}" target="_blank">PDF</a>'

            rows_html += f"""
            <tr>
                <td><code>{wf.workflow_id}</code></td>
                <td>{wf.question[:80]}...</td>
                <td><span class="badge {wf.stage.value.lower()}">{wf.stage.value}</span></td>
                <td>{wf.active_agent or 'None'}</td>
                <td><code>{wf.switch_room_id or '-'}</code></td>
                <td>{len(wf.records)} stages</td>
                <td>{report_links or '-'}</td>
            </tr>
            """

        if not rows_html:
            rows_html = "<tr><td colspan='7' style='text-align:center; padding: 2rem;'>No workflows yet. Use Telegram to submit a query!</td></tr>"

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>LabRelay Dashboard — Multi-Agent Research Workspace</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 1rem; margin-bottom: 2rem; }}
                h1 {{ margin: 0; font-size: 1.8rem; color: #38bdf8; display: flex; align-items: center; gap: 0.5rem; }}
                .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem; }}
                .card {{ background: #1e293b; padding: 1.25rem; border-radius: 8px; border: 1px solid #334155; }}
                .card-title {{ font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}
                .card-value {{ font-size: 1.75rem; font-weight: bold; margin-top: 0.5rem; color: #f1f5f9; }}
                table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; border: 1px solid #334155; }}
                th, td {{ padding: 1rem; text-align: left; border-bottom: 1px solid #334155; }}
                th {{ background: #0f172a; font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; }}
                .badge {{ padding: 0.25rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; }}
                .badge.completed {{ background: #065f46; color: #34d399; }}
                .badge.scouting, .badge.critical_review, .badge.experiment_design, .badge.experiment_execution, .badge.final_review {{ background: #854d0e; color: #fde047; }}
                .badge.failed, .badge.cancelled {{ background: #991b1b; color: #fca5a5; }}
                .btn {{ background: #0284c7; color: white; padding: 0.35rem 0.75rem; text-decoration: none; border-radius: 4px; font-size: 0.85rem; }}
                .btn:hover {{ background: #0369a1; }}
                .agent-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-top: 2rem; }}
                .agent-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 1rem; }}
                .agent-name {{ font-weight: bold; color: #38bdf8; }}
                .agent-role {{ font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem; }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>🔬 LabRelay Multi-Agent Workspace</h1>
                    <div>Engine: <strong>SandboxAQ Switch</strong> (<code>127.0.0.1:63457</code>)</div>
                </header>

                <div class="stats">
                    <div class="card">
                        <div class="card-title">Total Workflows</div>
                        <div class="card-value">{len(workflows)}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Active Agents</div>
                        <div class="card-value">4</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Switch Status</div>
                        <div class="card-value" style="color: #34d399;">Ready</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Telegram Bot</div>
                        <div class="card-value" style="color: #38bdf8;">@{settings.telegram_bot_username}</div>
                    </div>
                </div>

                <h2>Active Research Workflows</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Question</th>
                            <th>Stage</th>
                            <th>Active Agent</th>
                            <th>Switch Room</th>
                            <th>Stages</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>

                <h2>Switch Agent Team</h2>
                <div class="agent-grid">
                    <div class="agent-card">
                        <div class="agent-name">Research Scout</div>
                        <div class="agent-role">Literature Explorer (OpenAlex / Semantic Scholar)</div>
                    </div>
                    <div class="agent-card">
                        <div class="agent-name">Skeptic</div>
                        <div class="agent-role">Critical Academic Reviewer</div>
                    </div>
                    <div class="agent-card">
                        <div class="agent-name">Experimenter</div>
                        <div class="agent-role">Empirical Benchmark Engineer</div>
                    </div>
                    <div class="agent-card">
                        <div class="agent-name">Research Reviewer</div>
                        <div class="agent-role">Synthesis & Report Publisher</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    @app.get("/reports/md/{workflow_id}")
    async def get_markdown_report(workflow_id: str):
        path = settings.reports_dir / "markdown" / f"report_{workflow_id}.md"
        if not path.exists():
            raise HTTPException(status_code=404, detail="Markdown report not found")
        return FileResponse(path, media_type="text/markdown", filename=path.name)

    @app.get("/reports/pdf/{workflow_id}")
    async def get_pdf_report(workflow_id: str):
        path = settings.reports_dir / "pdf" / f"report_{workflow_id}.pdf"
        if not path.exists():
            raise HTTPException(status_code=404, detail="PDF report not found")
        return FileResponse(path, media_type="application/pdf", filename=path.name)

    return app

