import argparse
import logging
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse
import uvicorn

from .tools.record import registerRecordTools
from .tools.query import registerQueryTools
from .tools.reference import registerReferenceTools
from . import hooks

logging.basicConfig(level=logging.INFO)

mcp = FastMCP("ccmemory")

registerRecordTools(mcp)
registerQueryTools(mcp)
registerReferenceTools(mcp)


async def hookSessionStart(request: Request) -> JSONResponse:
    try:
        data = await request.json()
        result = hooks.handleSessionStart(
            session_id=data.get("session_id", ""), cwd=data.get("cwd", "")
        )
        return JSONResponse(result)
    except (ValueError, KeyError) as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def hookMessageResponse(request: Request) -> JSONResponse:
    try:
        data = await request.json()
        result = hooks.handleMessageResponse(
            session_id=data.get("session_id", ""),
            transcript_path=data.get("transcript_path", ""),
            cwd=data.get("cwd", ""),
        )
        return JSONResponse(result)
    except (ValueError, KeyError) as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def hookSessionEnd(request: Request) -> JSONResponse:
    try:
        data = await request.json()
        result = hooks.handleSessionEnd(
            session_id=data.get("session_id", ""),
            transcript_path=data.get("transcript_path"),
            cwd=data.get("cwd", ""),
        )
        return JSONResponse(result)
    except (ValueError, KeyError) as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def healthCheck(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


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
        hook_routes = [
            Route("/health", healthCheck, methods=["GET"]),
            Route("/hooks/session-start", hookSessionStart, methods=["POST"]),
            Route("/hooks/message-response", hookMessageResponse, methods=["POST"]),
            Route("/hooks/session-end", hookSessionEnd, methods=["POST"]),
        ]
        app = Starlette(
            routes=[
                *hook_routes,
                Mount("/", app=mcp.sse_app()),
            ]
        )
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
