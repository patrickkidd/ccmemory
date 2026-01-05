#!/usr/bin/env python3
"""Session end hook - finalize session.

Claude Code provides via stdin for SessionEnd:
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/dir",
  "hook_event_name": "SessionEnd",
  "reason": "clear|logout|prompt_input_exit|other"
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
    transcript_path = input_data.get("transcript_path")

    if not session_id:
        return

    try:
        client = getClient()
    except Exception:
        return

    transcript = ""
    if transcript_path and os.path.exists(transcript_path):
        try:
            with open(transcript_path, 'r') as f:
                transcript = f.read()
        except Exception:
            pass

    summary = f"Session ended at {datetime.now().isoformat()}"
    if transcript:
        lines = transcript.strip().split('\n')
        summary = f"Session with {len(lines)} message exchanges"

    try:
        client.endSession(
            session_id=session_id,
            transcript=transcript[:100000],
            summary=summary
        )

        client.recordTelemetry(
            event_type="session_end",
            project=os.path.basename(os.getcwd()),
            data={"session_id": session_id}
        )
    except Exception:
        pass

    print(json.dumps({"session_ended": session_id}))


if __name__ == "__main__":
    main()
