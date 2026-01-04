# ccmemory

**Persistent memory for Claude Code. The longer you use it, the smarter it gets.**

---

## The Problem

Every AI conversation starts from zero. You explain your project, your preferences, your constraints—then the session ends and it's all forgotten. Tomorrow, you're talking to a stranger again.

**ccmemory fixes this.** Decisions, corrections, and context accumulate over time. Session 50 is dramatically more effective than session 1.

```
Without memory:  Your input × 1.0 = Output  (always a stranger)
With ccmemory:   Your input × 3.0 = Output  (deep context, fewer mistakes)
```

### Not Just Another RAG Tool

| Capability | Copilot Work / Enterprise Search | ccmemory |
|------------|----------------------------------|----------|
| **Searches** | Existing docs and files | Decisions, corrections, reasoning |
| **Content created** | Before you search | During AI conversations |
| **Learning** | Static | Improves over time |
| **Preserves** | Information ("what") | Reasoning ("why") |

Enterprise search finds documents. ccmemory remembers why you made decisions.

---

## TLDR: 2-Minute Setup

### Individual Mode (Single Developer)

```bash
# 1. Clone and install
git clone https://github.com/patrickkidd/ccmemory
cd ccmemory && ./scripts/install.sh

# 2. Start the memory layer
ccmemory start

# 3. Open any Claude Code project — memory is now active
cd ~/your-project && claude
```

That's it. Decisions, corrections, and exceptions are captured automatically. They surface in future sessions.

### Team Mode (Shared Memory)

```bash
# 1. Deploy Neo4j (one-time, ops team)
docker run -d \
  --name ccmemory-team \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-team-password \
  -v ccmemory_team_data:/data \
  neo4j:5-community

# 2. Each developer
git clone https://github.com/patrickkidd/ccmemory
cd ccmemory && ./scripts/install.sh

# 3. Configure team connection (~/.bashrc or ~/.zshrc)
export CCMEMORY_USER_ID="$(git config user.email)"
export CCMEMORY_NEO4J_URI="bolt://your-team-server:7687"
export CCMEMORY_NEO4J_PASSWORD="your-team-password"

# 4. Work normally — curated decisions visible to team
cd ~/your-project && claude
```

---

## What It Does

Every Claude Code session generates valuable context that's lost when the session ends:
- Architectural decisions and their rationale
- Corrections to Claude's understanding
- Exceptions granted ("in this case, skip the test")
- Failed approaches and why they didn't work

**ccmemory captures this automatically**, then surfaces relevant precedent in future sessions.

### Before ccmemory
```
Session 1: "We use F1 scoring because precision matters more than recall here"
Session 2: "Why do we use F1 scoring?" → Re-explain from scratch
Session 3: "What's our scoring approach?" → Re-explain again
```

### After ccmemory
```
Session 1: "We use F1 scoring because precision matters more than recall here"
           → [Captured: Decision with rationale]
Session 2: "Why do we use F1 scoring?"
           → [Context injected: "Decision from Jan 3: F1 scoring chosen
              because precision > recall for this use case"]
```

---

## The Dashboard: A Thinking Surface

```bash
ccmemory dashboard
```

**For individuals**: A workspace for problem-solving, not vanity metrics.

- **Relevant history** — Past decisions that apply to your current work
- **Open questions** — Unresolved issues Claude flagged
- **What didn't work** — Failed approaches to avoid repeating
- **AI suggestions** — Patterns, hypotheses, and strategic considerations surfaced from your accumulated context

**For managers**: Team intelligence and business impact.

- **Cognitive coefficient** — Is the team's AI effectiveness improving over time?
- **Knowledge retention** — What happens when someone leaves?
- **Onboarding speed** — How fast do new hires reach productivity?
- **Loop efficiency** — How many iterations per human checkpoint?

---

## Enterprise Telemetry

The cognitive coefficient must correlate with real KPIs:

| ccmemory Metric | Business KPI | Correlation |
|-----------------|--------------|-------------|
| Re-explanation rate ↓ | Cycle time ↓ | Less context switching |
| Decision reuse ↑ | Defect rate ↓ | Fewer repeated mistakes |
| Correction velocity ↓ | Velocity ↑ | Faster course correction |
| Knowledge preservation ↑ | Onboarding time ↓ | Institutional memory persists |
| Loop efficiency ↑ | Developer leverage ↑ | More done per human checkpoint |

### For the C-Suite

```bash
ccmemory report --format=executive --period=quarterly
```

Generates measurable ROI:
- **Hours saved** from reduced re-explanation
- **Decisions preserved** vs. tribal knowledge lost
- **Onboarding acceleration** — new hires reach productivity faster
- **Cognitive coefficient trend** — is AI effectiveness compounding?

See [doc/TELEMETRY.md](doc/TELEMETRY.md) for the full enterprise metrics framework.

---

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Claude Code   │────▶│    ccmemory     │────▶│     Neo4j       │
│   (IDE/CLI)     │     │   (MCP Server)  │     │  (Graph Store)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │ Hooks capture         │ Detects decisions,    │ Stores with
        │ conversation          │ corrections,          │ relationships
        │                       │ exceptions            │
        ▼                       ▼                       ▼
   Session Start ──────▶ Query relevant ──────▶ Inject context
                         precedent              into Claude
```

### What Gets Captured

| Type | Example | Value |
|------|---------|-------|
| **Decision** | "Let's use retry with fixed delays, not exponential backoff" | Future sessions know why |
| **Correction** | "Actually, that endpoint returns JSON, not XML" | Claude doesn't repeat mistake |
| **Exception** | "Skip the linter for this file, it's generated code" | Rule-breaking is justified |
| **Failed Approach** | "Tried async but race conditions killed it" | Don't repeat failed experiments |
| **Q&A** | "What's the timeout?" → "30 seconds" | Constraints are remembered |

---

## Architecture

**Individual Mode**: One Neo4j container per machine, projects isolated by property.

**Team Mode**: Shared Neo4j server, developers identified by `CCMEMORY_USER_ID`.
- `developmental` decisions: Only visible to creator
- `curated` decisions: Visible to all team members (promoted via git hooks)

### Scope

**Phase 1 (Current)**: Software development focus — decisions, corrections, and context for Claude Code sessions. This is the MVP that ships.

**Future Phases**: The architecture generalizes to any domain requiring accumulated understanding: career consulting, medical research, relationship systems, strategic planning. See the Vision doc for the full picture.

See [doc/PROJECT_VISION.md](doc/PROJECT_VISION.md) for the full conceptual architecture (multi-domain, active research, hypothesis generation).
See [doc/IMPLEMENTATION_PLAN.md](doc/IMPLEMENTATION_PLAN.md) for Phase 1 build specifications.

---

## Requirements

- Docker (for Neo4j)
- Python 3.10+
- Claude Code CLI

---

## Inspiration

This project builds on ideas from [AI's trillion-dollar opportunity: Context graphs](https://foundationcapital.com/ais-trillion-dollar-opportunity-context-graphs/) by Gupta & Garg at Foundation Capital — the insight that AI tools fragment organizational knowledge across sessions, and that capturing decision traces (not just state) is where the real value lies.

---

## License

Apache 2.0
