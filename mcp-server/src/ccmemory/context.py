"""Session context for MCP tools.

The session_start hook sets the current project, which tools can then access.
This avoids needing to pass project through MCP protocol or use os.getcwd().
"""

_current_project: str | None = None
_current_session_id: str | None = None


def setCurrentSession(project: str, session_id: str):
    """Called by session_start hook to set current context."""
    global _current_project, _current_session_id
    _current_project = project
    _current_session_id = session_id


def clearCurrentSession():
    """Called by session_end hook to clear context."""
    global _current_project, _current_session_id
    _current_project = None
    _current_session_id = None


def getCurrentProject() -> str | None:
    """Get the current project name, or None if no session active."""
    return _current_project


def getCurrentSessionId() -> str | None:
    """Get the current session ID, or None if no session active."""
    return _current_session_id
