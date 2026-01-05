"""MCP server for ccmemory."""

import asyncio
from mcp.server.fastmcp import FastMCP

from .tools.record import registerRecordTools
from .tools.query import registerQueryTools
from .tools.reference import registerReferenceTools

mcp = FastMCP("ccmemory")

# Register all tools
registerRecordTools(mcp)
registerQueryTools(mcp)
registerReferenceTools(mcp)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
