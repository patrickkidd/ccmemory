import argparse
import logging
from mcp.server.fastmcp import FastMCP

from .tools.record import registerRecordTools
from .tools.query import registerQueryTools
from .tools.reference import registerReferenceTools

logging.basicConfig(level=logging.INFO)

mcp = FastMCP("ccmemory")

registerRecordTools(mcp)
registerQueryTools(mcp)
registerReferenceTools(mcp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Run as HTTP server")
    parser.add_argument("--port", type=int, default=8766, help="HTTP port")
    parser.add_argument("--init-schema", action="store_true", help="Initialize Neo4j schema")
    args = parser.parse_args()

    if args.init_schema or args.http:
        from .graph import GraphClient
        GraphClient(init_schema=True)

    if args.http:
        mcp.run(transport="sse", port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
