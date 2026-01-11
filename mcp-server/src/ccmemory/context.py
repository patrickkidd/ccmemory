"""Project context for MCP tools.

Per doc/clarifications/1-DAG-with-CROSS-REFS.md:
- No session tracking, just project context
- Tools use this to know which project they're operating on
"""

_current_project: str | None = None


def setCurrentProject(project: str):
    """Called by session_start hook to set current project context."""
    global _current_project
    _current_project = project


def clearCurrentProject():
    """Called by session_end hook to clear context."""
    global _current_project
    _current_project = None


def getCurrentProject() -> str | None:
    """Get the current project name, or None if no session active."""
    return _current_project
