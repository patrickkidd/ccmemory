# ccmemory

**Persistent memory for Claude Code. Never re-explain context again.**

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

## Immediate Value: The Dashboard

From day one, you get visibility into your development knowledge:

```bash
ccmemory dashboard
```

Opens a browser showing:
- **Decision timeline** — What was decided, when, by whom
- **Correction frequency** — How often Claude's understanding gets corrected
- **Exception patterns** — Rules that keep getting broken (maybe they're bad rules)
- **Knowledge gaps** — Topics with many questions, few decisions

Even before the AI uses this data, *you* can see your accumulated institutional knowledge.

---

## Enterprise Telemetry

ccmemory tracks metrics that matter to leadership:

| Metric | What It Measures | Why It Matters |
|--------|------------------|----------------|
| **Re-explanation Rate** | How often the same context is re-provided | Direct time savings |
| **Decision Reuse** | How often past decisions inform current work | Institutional knowledge compounding |
| **Correction Velocity** | Time from wrong → right understanding | Learning speed |
| **Cross-Session Continuity** | % of sessions that reference prior context | Memory effectiveness |
| **Time-to-Context** | Seconds to surface relevant precedent | Developer wait time |

### For the C-Suite

```bash
ccmemory report --format=executive --period=quarterly
```

Generates:
- **Hours saved** from reduced re-explanation (measurable)
- **Decisions preserved** vs. tribal knowledge (quantifiable risk reduction)
- **Knowledge graph growth** over time (institutional asset building)
- **Team knowledge sharing** metrics (collaboration visibility)

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

See [doc/PROJECT_VISION.md](doc/PROJECT_VISION.md) for the full conceptual architecture.
See [doc/IMPLEMENTATION_PLAN.md](doc/IMPLEMENTATION_PLAN.md) for build specifications.

---

## Requirements

- Docker (for Neo4j)
- Python 3.10+
- Claude Code CLI

---

## License

MIT
