# ccmemory

A Claude Code plugin for persistent context management. Stop re-explaining your project every session.

## What It Does

- **Automatic session hooks** - Loads previous context at start, reminds to save at end
- **Semantic memory** - Vector database for storing/retrieving project facts
- **Doc index** - Makes your existing documentation discoverable
- **Memory skill** - Teaches Claude how to use the memory system

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

The plugin registers these hooks:

| Event | Action |
|-------|--------|
| **SessionStart** | Creates `.ccmemory/` if missing, loads `session.md` context |
| **UserPromptSubmit** | Analyzes each message for memory triggers, injects reminder |
| **Stop** | Reminds you to update `session.md` before ending |

### Trigger Detection

The `UserPromptSubmit` hook automatically detects when you say things like:
- **Corrections**: "No, that's wrong", "I already told you", "Stop doing X"
- **Decisions**: "I've decided", "Let's use X", "The approach will be"
- **Preferences**: "I prefer", "Always do X", "Never do Y"
- **Facts**: "The way X works", "Watch out for", "Gotcha"

When detected, Claude receives a reminder to store the information to memory.

### Project Structure

On first session in a project, the plugin creates:

```
your-project/
└── .ccmemory/
    ├── chroma.db      # Vector database (auto-created by memory service)
    ├── doc-index.md   # Your documentation inventory
    └── session.md     # Session handoff notes
```

### Memory Skill

The plugin includes a skill that teaches Claude:
- How to check session context at start
- When to store important facts
- How to update session.md at end
- How to use the doc-index

## Usage

### First Time Setup

1. Install the plugin (see above)
2. Start Claude Code in your project
3. The plugin auto-creates `.ccmemory/`
4. Edit `.ccmemory/doc-index.md` to list your project docs

### Each Session

1. **Start**: Plugin loads previous session context automatically
2. **Work**: Claude uses memory skill to track important facts
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
