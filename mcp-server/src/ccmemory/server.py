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


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "cat": getattr(record, "cat", "mcp"),
            "event": getattr(record, "event", record.funcName),
            "project": getattr(record, "project", ""),
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
    log_path = os.getenv("CCMEMORY_LOG_PATH", "/logs/mcp.log")
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    handler = RotatingFileHandler(log_path, maxBytes=10 * 1024 * 1024, backupCount=3)
    handler.setFormatter(JsonFormatter())

    logger = logging.getLogger("ccmemory")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


logging.basicConfig(level=logging.INFO)
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
    try:
        result = hooks.handleSessionStart(
            session_id=session_id,
            cwd=data.get("cwd", ""),
            conversation_stems=data.get("conversation_stems"),
        )
        logger.info(
            "",
            extra={
                "cat": "hook",
                "event": "session-start",
                "project": project,
                "duration_ms": int((time.time() - start) * 1000),
                "data": {"session_id": session_id},
            },
        )
        return JSONResponse(result)
    except (ValueError, KeyError) as e:
        logger.warning(
            str(e),
            extra={
                "cat": "hook",
                "event": "session-start",
                "project": project,
                "data": {"session_id": session_id},
            },
        )
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        logger.exception(
            "",
            extra={
                "cat": "hook",
                "event": "session-start",
                "project": project,
                "data": {"session_id": session_id},
            },
        )
        return JSONResponse({"error": str(e)}, status_code=500)


async def hookMessageResponse(request: Request) -> JSONResponse:
    start = time.time()
    data = await request.json()
    project = data.get("cwd", "").rsplit("/", 1)[-1]
    session_id = data.get("session_id", "")
    try:
        result = hooks.handleMessageResponse(
            session_id=session_id,
            transcript_path=data.get("transcript_path", ""),
            cwd=data.get("cwd", ""),
        )
        logger.info(
            "",
            extra={
                "cat": "hook",
                "event": "message-response",
                "project": project,
                "duration_ms": int((time.time() - start) * 1000),
                "data": {
                    "session_id": session_id,
                    "detections": result.get("detections", 0),
                },
            },
        )
        return JSONResponse(result)
    except (ValueError, KeyError) as e:
        logger.warning(
            str(e),
            extra={
                "cat": "hook",
                "event": "message-response",
                "project": project,
                "data": {"session_id": session_id},
            },
        )
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        logger.exception(
            "",
            extra={
                "cat": "hook",
                "event": "message-response",
                "project": project,
                "data": {"session_id": session_id},
            },
        )
        return JSONResponse({"error": str(e)}, status_code=500)


async def hookSessionEnd(request: Request) -> JSONResponse:
    start = time.time()
    data = await request.json()
    project = data.get("cwd", "").rsplit("/", 1)[-1]
    session_id = data.get("session_id", "")
    try:
        result = hooks.handleSessionEnd(
            session_id=session_id,
            transcript_path=data.get("transcript_path"),
            cwd=data.get("cwd", ""),
        )
        logger.info(
            "",
            extra={
                "cat": "hook",
                "event": "session-end",
                "project": project,
                "duration_ms": int((time.time() - start) * 1000),
                "data": {"session_id": session_id},
            },
        )
        return JSONResponse(result)
    except (ValueError, KeyError) as e:
        logger.warning(
            str(e),
            extra={
                "cat": "hook",
                "event": "session-end",
                "project": project,
                "data": {"session_id": session_id},
            },
        )
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        logger.exception(
            "",
            extra={
                "cat": "hook",
                "event": "session-end",
                "project": project,
                "data": {"session_id": session_id},
            },
        )
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

    logger.info(
        "",
        extra={
            "cat": "tool",
            "event": "bulk-import",
            "project": project,
            "duration_ms": int((time.time() - start) * 1000),
            "data": stats,
        },
    )
    return JSONResponse(stats)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Run as HTTP server")
    parser.add_argument("--port", type=int, default=8766, help="HTTP port")
    parser.add_argument(
        "--init-schema", action="store_true", help="Initialize Neo4j schema"
    )
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
            Route("/api/bulk-import", bulkImport, methods=["POST"]),
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
