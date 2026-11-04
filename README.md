# LabRelay — Multi-Agent AI Research Workspace Using Switch

LabRelay is a Telegram-first academic research workspace that coordinates specialized AI agents in a shared **Switch** collaboration room to produce peer-reviewed, reproducible research assessments.

---

## 🏛️ Architecture Overview

```
 Telegram User
      │
      ▼ (Commands: /research, /status, /report, /cancel, /reset)
┌─────────────────────────────────────────────────────────────┐
│                   LabRelay Telegram Bot                     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ (State Machine)
┌─────────────────────────────────────────────────────────────┐
│            LabRelay Multi-Agent Research Runner             │
└──────────────────────────────┬──────────────────────────────┘
                               │
               Switch Room & Protocol Collaboration
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
┌──────────────┐       ┌──────────────┐       ┌─────────────────┐
│Research Scout│◄─────►│   Skeptic    │◄─────►│   Experimenter  │
└──────────────┘       └──────────────┘       └────────┬────────┘
  (OpenAlex /            (Methodology &                │
Semantic Scholar)        Novelty Check)                ▼
                                              ┌─────────────────┐
                                              │ Research Reviewer│
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                            12-Section Research Report
                                            (Markdown & PDF Export)
```

---

## 🤖 The 4 Specialized Switch Agents

1. **Research Scout** (`research-scout`):
   - Formulates academic literature queries against OpenAlex and Semantic Scholar.
   - Extracts real paper titles, verified DOIs, author lists, and publication details.
   - Strictly avoids fabrication of citations or novelty claims.

2. **Skeptic** (`research-skeptic`):
   - Critically analyzes literature findings and methodology.
   - Challenges distance metric concentration, spherical centroid assumptions in K-Means, and $O(N^2)$ space/time bottlenecks in Hierarchical clustering.
   - Identifies genuine research gaps vs already solved problems.

3. **Experimenter** (`research-experimenter`):
   - Formulates concrete empirical benchmarks with datasets, baselines, and metrics.
   - Executes sandboxed Python validation code within the project workspace.
   - Reports actual experimental outcomes separately from theoretical expectations.

4. **Research Reviewer** (`research-reviewer`):
   - Performs academic peer review across all findings.
   - Synthesizes findings into a formal 12-section research report.
   - Exports the report in both **Markdown (`.md`)** and **PDF (`.pdf`)** formats.

---

## 🔄 Research Workflow State Machine

```
RECEIVED ──► SCOUTING ──► CRITICAL_REVIEW ──► EXPERIMENT_DESIGN ──► EXPERIMENT_EXECUTION ──► FINAL_REVIEW ──► COMPLETED
    │            │               │                    │                      │                     │
    └────────────┴───────────────┴────────────────────┴──────────────────────┴─────────────────────┴──► CANCELLED / FAILED
```

Every stage records its input, output, executing agent, and timestamps.

---

## 🔌 SandboxAQ Switch Setup & Integration

LabRelay uses **SandboxAQ Switch** as its multi-agent communication fabric, room management layer, and agent coordination bus.

### 1. Switch Architecture & Port Allocations
A standard local Switch installation consists of:

| Component | Default Endpoint / Port | Purpose |
|---|---|---|
| **Switch Core API** | `http://127.0.0.1:63457` | Gateway auth, agent registration, room creation, and REST operations |
| **PostgreSQL Event Bus** | `127.0.0.1:63459` | High-throughput `LISTEN/NOTIFY` channel for room activity and signals |
| **Collaboration Gateway** | `127.0.0.1:63456` | Inbound callbacks and external messaging bridges |
| **Agent WebSocket Bus** | `ws://127.0.0.1:63457/agents/{id}/connection/ws` | Real-time presence, bi-directional event streaming, and targeted handoffs |

---

### 2. How to Start Switch

Depending on your installation, you can run Switch via the desktop application or headless CLI:

#### Method A: Using Switch Console (Desktop App)
1. Launch **Switch Console.app** on macOS:
   ```bash
   open -a "Switch Console"
   ```
2. The desktop console automatically initializes the local PostgreSQL engine and starts Switch Core on port `63457`.

#### Method B: Headless Native Services (Terminal / Background)
If running headless or on a development workstation without the GUI open:

```bash
# 1. Start the Switch PostgreSQL Database Engine
"$HOME/Library/Application Support/switchdash/local-switch-server/native/toolchain/bundle-28d02ed370b4/postgres/bin/pg_ctl" \
  -D "$HOME/Library/Application Support/switchdash/local-switch-server/native/pgdata" \
  -l "$HOME/Library/Application Support/switchdash/local-switch-server/native/logs/postgres.log" start

# 2. Launch the Switch Core Server Daemon
env $(cat "$HOME/Library/Application Support/switchdash/local-switch-server/native/run/switch-core.env" | grep -v '^#' | xargs) \
  "$HOME/Library/Application Support/switchdash/local-switch-server/native/switch-core/0.31.0/venv/bin/switch-core"
```

---

### 3. Verifying Switch Health & Readiness

Confirm both the server and event bus are healthy before starting LabRelay:

```bash
# Check basic API availability
curl -s http://127.0.0.1:63457/health
# Expected: {"status":"ok"}

# Verify readiness of database, listeners, and bridges
curl -s http://127.0.0.1:63457/health/ready
```

A healthy response confirms all subsystems are operational:
```json
{
  "status": "ready",
  "checks": {
    "database": { "healthy": true },
    "message_listener": { "healthy": true },
    "session_activity_listener": { "healthy": true },
    "agent_event_listener": { "healthy": true },
    "signal_bus": { "healthy": true },
    "bridges": { "healthy": true },
    "connectors": { "healthy": true }
  }
}
```

---

### 4. How LabRelay Interacts with Switch
When a research query is submitted via Telegram:

1. **Authentication (`/gateway/admin/login`)**:
   LabRelay authenticates using the gateway admin credentials and acquires a session cookie.
2. **Team Registration (`/gateway/agents/register-other`)**:
   Registers the four agents (`research-scout`, `research-skeptic`, `research-experimenter`, `research-reviewer`) and provisions dedicated API keys.
3. **Room Provisioning (`POST /gateway/chats`)**:
   Spins up an isolated collaboration chat room for the specific research workflow (e.g. `LabRelay Research: what if...`).
4. **Targeted Agent Handoffs (`/ops/send_targeted_message`)**:
   Agents communicate in sequence through targeted room mentions (`send_targeted_message`), allowing full observability of the reasoning chain.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+ (Python 3.14 supported).
- Local Switch installation running (`http://127.0.0.1:63457`).
- Telegram account.

### 2. Setup Environment
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure `.env`
Ensure `.env` contains your Telegram Bot Token and Switch configuration:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_BOT_USERNAME=deepak_labrelay_bot
SWITCH_API_URL=http://127.0.0.1:63457
SWITCH_GATEWAY_ADMIN_EMAIL=admin@switch.local
SWITCH_GATEWAY_ADMIN_PASSWORD=your_gateway_admin_password_here
```

### 4. Run the Application
```bash
./venv/bin/python3 -m labrelay.app
```

---

## 📱 Telegram Bot Commands

Open Telegram and chat with [@deepak_labrelay_bot](https://t.me/deepak_labrelay_bot):

| Command | Action |
|---|---|
| `/start` | Introduces LabRelay and explains its capabilities |
| `/help` | Displays command guidance and examples |
| `/research <question>` | Starts an autonomous research workflow across the 4 Switch agents |
| `/status` | Shows the active workflow stage, current working agent, and Switch room |
| `/report` | Retrieves the latest completed research report (both Markdown and PDF) |
| `/cancel` | Safely cancels the active research workflow |
| `/reset` | Clears conversation state to start fresh |

### Example Query
```text
/research I want to investigate whether clustering algorithms can identify meaningful structures in high-dimensional scientific datasets. Compare K-Means, PAM, and hierarchical clustering, identify limitations, and propose an experiment.
```

---

## 🧪 Testing

Run the full automated test suite:
```bash
./venv/bin/pytest -v tests/
```
Output:
```text
tests/test_experiment.py::test_experiment_safety_validation PASSED
tests/test_experiment.py::test_experiment_execution_success PASSED
tests/test_experiment.py::test_clustering_benchmark PASSED
tests/test_report.py::test_report_generation PASSED
tests/test_sources.py::test_academic_paper_citation_format PASSED
tests/test_sources.py::test_openalex_live_search PASSED
tests/test_switch.py::test_switch_gateway_health_and_auth PASSED
tests/test_switch.py::test_switch_agent_team_registration PASSED
tests/test_workflow.py::test_state_machine_valid_transitions PASSED
tests/test_workflow.py::test_state_machine_invalid_transition PASSED
tests/test_workflow.py::test_workflow_cancellation PASSED
tests/test_workflow.py::test_workflow_model PASSED
======================== 12 passed in 2.97s ========================
```

---

## 🛡️ Security & Privacy
- Zero hardcoded credentials; all secrets stored in `.env` (ignored by git).
- Validated Telegram user authentication and access restriction capability.
- Experiments execute strictly inside sandboxed project directories with timeouts and pattern filtering.
- Research outputs are never published or distributed externally without explicit human authorization.

