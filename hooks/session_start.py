#!/usr/bin/env python3
"""Session start hook - inject relevant context.

Claude Code provides via stdin:
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/dir",
  "hook_event_name": "SessionStart",
  "source": "startup|resume|clear|compact"
}
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server', 'src'))

from ccmemory.graph import getClient


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    session_id = input_data.get("session_id")
    cwd = input_data.get("cwd", os.getcwd())
    project = os.path.basename(cwd)

    if not session_id:
        return

    try:
        client = getClient()

        client.createSession(
            session_id=session_id,
            project=project,
            started_at=datetime.now().isoformat()
        )

        recent = client.queryRecent(project, limit=15)
        stale = client.queryStaleDecisions(project, days=30)
        failed = client.queryFailedApproaches(project, limit=5)

        context_parts = []

        context_parts.append(f"# Context Graph: {project}")
        context_parts.append(f"Session: {session_id[:12]}...")
        context_parts.append("")

        if recent:
            context_parts.append("## Recent Context")
            for item in recent[:10]:
                node = item.get('n', {})
                if not node:
                    continue
                if 'description' in node:
                    context_parts.append(f"- Decision: {str(node['description'])[:100]}")
                elif 'wrong_belief' in node:
                    context_parts.append(f"- Correction: {str(node['right_belief'])[:100]}")
                elif 'summary' in node:
                    context_parts.append(f"- Insight: {str(node['summary'])[:100]}")

        if stale:
            context_parts.append("")
            context_parts.append("## Decisions Needing Review")
            for d in stale[:3]:
                context_parts.append(f"- {str(d.get('description', ''))[:80]} (developmental, may need revisit)")

        if failed:
            context_parts.append("")
            context_parts.append("## Failed Approaches (Don't Repeat)")
            for f in failed[:3]:
                context_parts.append(f"- {str(f.get('approach', ''))[:60]}: {str(f.get('lesson', ''))[:60]}")

        if not recent and not stale and not failed:
            context_parts.append("No prior context. Decisions, corrections, and insights will be captured.")

        print("\n".join(context_parts))

    except Exception as e:
        print(f"# Context Graph: {project}")
        print(f"Connection error: {e}")
        print("Neo4j may not be running. Start with: ccmemory start")


if __name__ == "__main__":
    main()
