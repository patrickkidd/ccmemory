import argparse
import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse
import uvicorn

from .tools.record import registerRecordTools
from .tools.query import registerQueryTools
from .tools.reference import registerReferenceTools
from .tools.backfill import registerBackfillTools
from . import hooks
from . import activitylog  # noqa: F401 - sets up activity log handler


class JsonFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        self.user_id = os.getenv("CCMEMORY_USER_ID", "")

    def format(self, record):
        entry = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "cat": getattr(record, "cat", "mcp"),
            "event": getattr(record, "event", record.funcName),
            "project": getattr(record, "project", ""),
            "user": self.user_id,
        }
        if record.getMessage():
            entry["msg"] = record.getMessage()
        if hasattr(record, "duration_ms"):
            entry["duration_ms"] = record.duration_ms
        if hasattr(record, "data"):
            entry["data"] = record.data
        if record.exc_info:
            entry["error"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def setupLogging():
    log_path = os.getenv("CCMEMORY_MCP_LOG", "instance/mcp.jsonl")
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    handler = RotatingFileHandler(log_path, maxBytes=10 * 1024 * 1024, backupCount=3)
    handler.setFormatter(JsonFormatter())

    logger = logging.getLogger("ccmemory")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


logging.basicConfig(level=logging.DEBUG)
logger = setupLogging()

mcp = FastMCP("ccmemory")

registerRecordTools(mcp)
registerQueryTools(mcp)
registerReferenceTools(mcp)
registerBackfillTools(mcp)


async def hookSessionStart(request: Request) -> JSONResponse:
    start = time.time()
    data = await request.json()
    project = data.get("cwd", "").rsplit("/", 1)[-1]
    session_id = data.get("session_id", "")
    logger.info(f"<- POST /hooks/session-start (project={project})")
    logger.debug(f"session_id={session_id}")
    try:
        result = hooks.handleSessionStart(
            session_id=session_id,
            cwd=data.get("cwd", ""),
            conversation_stems=data.get("conversation_stems"),
        )
        duration = int((time.time() - start) * 1000)
        context_len = len(result.get("context", ""))
        logger.info(f"-> 200 (context: {context_len} chars, {duration}ms)")
        return JSONResponse(result)
    except (ValueError, KeyError) as e:
        logger.warning(f"-> 400: {e}")
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        logger.exception(f"-> 500: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def hookMessageResponse(request: Request) -> JSONResponse:
    start = time.time()
    data = await request.json()
    project = data.get("cwd", "").rsplit("/", 1)[-1]
    session_id = data.get("session_id", "")
    logger.info(f"<- POST /hooks/message-response (project={project})")
    try:
        result = await hooks.handleMessageResponse(
            session_id=session_id,
            transcript_path=data.get("transcript_path", ""),
            cwd=data.get("cwd", ""),
        )
        duration = int((time.time() - start) * 1000)
        detections = result.get("detections", 0)
        logger.info(f"-> 200 (detections={detections}, {duration}ms)")
        return JSONResponse(result)
    except (ValueError, KeyError) as e:
        logger.warning(f"-> 400: {e}")
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        logger.exception(f"-> 500: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def hookSessionEnd(request: Request) -> JSONResponse:
    start = time.time()
    data = await request.json()
    project = data.get("cwd", "").rsplit("/", 1)[-1]
    session_id = data.get("session_id", "")
    logger.info(f"<- POST /hooks/session-end (project={project})")
    try:
        result = hooks.handleSessionEnd(
            session_id=session_id,
            transcript_path=data.get("transcript_path"),
            cwd=data.get("cwd", ""),
        )
        duration = int((time.time() - start) * 1000)
        logger.info(f"-> 200 ({duration}ms)")
        return JSONResponse(result)
    except (ValueError, KeyError) as e:
        logger.warning(f"-> 400: {e}")
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        logger.exception(f"-> 500: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def healthCheck(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def bulkImport(request: Request) -> JSONResponse:
    from .backfill import backfillConversationContent

    start = time.time()
    data = await request.json()
    project = data.get("project", "")
    conversations = data.get("conversations", [])

    if not project:
        return JSONResponse({"error": "project required"}, status_code=400)

    logger.info(
        f"<- POST /api/bulk-import (project={project}, count={len(conversations)})"
    )

    stats = {
        "processed": 0,
        "skipped": 0,
        "detections": 0,
    }

    for conv in conversations:
        session_id = conv.get("session_id", "")
        content = conv.get("content", "")
        if not session_id or not content:
            stats["skipped"] += 1
            continue

        try:
            result = await backfillConversationContent(
                project=project,
                session_id=session_id,
                jsonl_content=content,
            )
            if result.get("already_imported"):
                stats["skipped"] += 1
            else:
                stats["processed"] += 1
                stats["detections"] += result.get("detections_stored", 0)
        except Exception as e:
            logger.warning(f"Bulk import error: {e}")
            stats["skipped"] += 1

    duration = int((time.time() - start) * 1000)
    logger.info(
        f"-> 200 (processed={stats['processed']}, skipped={stats['skipped']}, {duration}ms)"
    )
    return JSONResponse(stats)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Run as HTTP server")
    parser.add_argument("--port", type=int, default=8766, help="HTTP port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument(
        "--init-schema", action="store_true", help="Initialize Neo4j schema"
    )
    args = parser.parse_args()

    if args.init_schema or args.http:
        from .graph import GraphClient

        GraphClient(init_schema=True)

    if args.http:
        logger.info(f"Starting HTTP server on port {args.port}")
        if args.reload:
            uvicorn.run(
                "ccmemory.server:createApp",
                factory=True,
                host="0.0.0.0",
                port=args.port,
                reload=True,
                reload_dirs=["src"],
            )
        else:
            uvicorn.run(createApp(), host="0.0.0.0", port=args.port)
    else:
        mcp.run()


def createApp():
    hook_routes = [
        Route("/health", healthCheck, methods=["GET"]),
        Route("/hooks/session-start", hookSessionStart, methods=["POST"]),
        Route("/hooks/message-response", hookMessageResponse, methods=["POST"]),
        Route("/hooks/session-end", hookSessionEnd, methods=["POST"]),
        Route("/api/bulk-import", bulkImport, methods=["POST"]),
    ]
    return Starlette(
        routes=[
            *hook_routes,
            Mount("/", app=mcp.sse_app()),
        ]
    )


if __name__ == "__main__":
    main()
