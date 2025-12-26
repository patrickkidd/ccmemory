# ccmemory

A Claude Code plugin for persistent context management. Stop re-explaining your project every session.

## What It Does

- **Automatic trigger detection** - Detects corrections, decisions, preferences, and facts in your messages
- **Session hooks** - Loads previous context at start, reminds to save at end
- **Semantic memory** - Vector database for storing/retrieving project facts
- **Memory skill** - Teaches Claude mandatory capture patterns

## Installation

### Option 1: From GitHub (Recommended)

```bash
# Add the marketplace (one-time)
claude /plugin add-marketplace https://raw.githubusercontent.com/patrickkidd/ccmemory/main/marketplace.json

# Install the plugin
claude /plugin install ccmemory
```

### Option 2: Local Installation

```bash
git clone https://github.com/patrickkidd/ccmemory.git ~/.claude/plugins/ccmemory
```

### Prerequisite: mcp-memory-service

The plugin requires mcp-memory-service for semantic memory:

```bash
npm install -g mcp-memory-service
```

## How It Works

### Automatic Hooks

| Event | Script | Action |
|-------|--------|--------|
| **SessionStart** | `load-memory.sh` | Creates `.ccmemory/` if missing, loads `session.md` context |
| **UserPromptSubmit** | `check-triggers.sh` | Analyzes each message for memory triggers, injects reminder |
| **Stop** | `save-memory.sh` | Reminds you to update `session.md` before ending |

### Trigger Detection

The `UserPromptSubmit` hook automatically detects when you say things like:

| Trigger Type | Example Patterns |
|--------------|------------------|
| **Corrections** | "No, that's wrong", "I already told you", "Stop doing X", "That's not how it works" |
| **Decisions** | "I've decided", "Let's use X", "The approach will be", "We'll go with" |
| **Preferences** | "I prefer", "Always do X", "Never do Y", "Make sure to" |
| **Facts** | "The way X works", "Watch out for", "Gotcha", "This is because" |

When detected, Claude receives:
```
<ccmemory-trigger type="CORRECTION">
IMPORTANT: The user's message contains information that should be stored to memory.
After processing this message, use the memory service to store the key information.
Then confirm: "Stored to memory: [brief description]"
</ccmemory-trigger>
```

### Memory Skill

The plugin includes a skill (`skills/memory/SKILL.md`) that teaches Claude:

- **Mandatory capture triggers** - When to store information (corrections highest priority)
- **Self-check protocol** - After each message, check if any trigger fired
- **Storage routing** - Memory service vs session.md vs project docs
- **Session protocols** - What to do at start and end of sessions

### Project Structure

On first session in a project, the plugin creates:

```
your-project/
└── .ccmemory/
    ├── chroma.db      # Vector database (auto-created by memory service)
    ├── doc-index.md   # Your documentation inventory
    └── session.md     # Session handoff notes
```

## Usage

### First Time Setup

1. Install the plugin (see above)
2. Install mcp-memory-service: `npm install -g mcp-memory-service`
3. Start Claude Code in your project
4. The plugin auto-creates `.ccmemory/`
5. Edit `.ccmemory/doc-index.md` to list your project docs

### Each Session

1. **Start**: Plugin loads previous session context automatically
2. **Work**: Trigger detection injects reminders when you share important info
3. **End**: Plugin reminds you to update session.md

### Customizing doc-index.md

List your project's documentation:

```markdown
| File | Purpose |
|------|---------|
| docs/API.md | REST API reference |
| docs/ARCHITECTURE.md | System design overview |
| CLAUDE.md | Project-specific Claude instructions |
```

## Plugin Structure

```
ccmemory/
├── .claude-plugin/
│   └── plugin.json        # Plugin manifest
├── hooks/
│   └── hooks.json         # SessionStart/UserPromptSubmit/Stop hooks
├── scripts/
│   ├── load-memory.sh     # Runs at session start
│   ├── check-triggers.sh  # Analyzes user messages for triggers
│   └── save-memory.sh     # Runs at session end
├── skills/
│   └── memory/
│       └── SKILL.md       # Memory management skill
├── templates/
│   ├── doc-index.md       # Doc inventory template
│   └── session-template.md
└── .mcp.json              # Memory server config
```

## Updating the Plugin

### If installed via marketplace:

```bash
claude /plugin update ccmemory
```

### If installed locally (git clone):

```bash
cd ~/.claude/plugins/ccmemory
git pull
```

Restart Claude Code after updating for changes to take effect.

## Requirements

- Claude Code CLI
- Node.js 18+ (for mcp-memory-service)

## License

MIT
