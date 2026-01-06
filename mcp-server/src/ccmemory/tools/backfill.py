"""MCP tools for backfilling historical data."""

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .logging import logTool


def registerBackfillTools(mcp: FastMCP):
    """Register all backfill tools with the MCP server."""

    @mcp.tool()
    @logTool
    async def ccmemory_list_conversations() -> dict:
        """List all JSONL conversation files for the CURRENT project.

        USE THIS TOOL FIRST when user asks to import/backfill conversation history.
        Returns the project name, folder path, and list of session IDs to import.

        The tool automatically determines the correct folder based on cwd.
        """
        cwd = os.getcwd()
        project = os.path.basename(cwd)
        folder_name = cwd.replace("/", "-")
        if folder_name.startswith("-"):
            folder_name = folder_name[1:]
        folder_name = "-" + folder_name

        claude_projects = Path.home() / ".claude" / "projects" / folder_name
        if not claude_projects.exists():
            return {
                "project": project,
                "folder": str(claude_projects),
                "exists": False,
                "sessions": [],
                "count": 0,
            }

        sessions = []
        for f in claude_projects.glob("*.jsonl"):
            if f.stat().st_size > 0:
                sessions.append(f.stem)

        return {
            "project": project,
            "folder": str(claude_projects),
            "exists": True,
            "sessions": sorted(sessions),
            "count": len(sessions),
        }

    @mcp.tool()
    @logTool
    async def ccmemory_backfill_conversation(
        project: str,
        session_id: str,
        jsonl_content: str,
        dry_run: bool = False
    ) -> dict:
        """Import a Claude Code JSONL conversation file into ccmemory's context graph.

        USE ccmemory_list_conversations FIRST to get the list of sessions to import.
        Then call this tool once per session_id, reading the file content first.

        Args:
            project: Project name from ccmemory_list_conversations
            session_id: Session ID from ccmemory_list_conversations
            jsonl_content: The complete JSONL file content as a string
            dry_run: If true, preview without storing
        """
        from ..backfill import backfillConversationContent
        return await backfillConversationContent(project, session_id, jsonl_content, dry_run)

    @mcp.tool()
    @logTool
    async def ccmemory_backfill_markdown(
        project: str,
        file_path: str,
        content: str,
        dry_run: bool = False
    ) -> dict:
        """Import a markdown file into ccmemory's context graph.

        USE THIS TOOL when user asks to import/backfill markdown docs into ccmemory.
        Decision logs (## YYYY-MM-DD: Title format) become Decision nodes.

        Args:
            project: Project name (e.g. "theapp")
            file_path: Relative path (e.g. "doc/decisions.md")
            content: The complete markdown file content as a string
            dry_run: If true, preview without storing
        """
        from ..backfill import backfillMarkdownContent
        return await backfillMarkdownContent(project, file_path, content, dry_run)
