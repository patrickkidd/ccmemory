"""Flask dashboard for ccmemory."""

from gevent import monkey

monkey.patch_all()

import hashlib
import io
import json
import os
import time
import uuid
import zipfile
from datetime import datetime

from flask import Flask, render_template, jsonify, request
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
from neo4j import GraphDatabase

app = Flask(__name__)
app.debug = False
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max upload

MCP_LOG = os.getenv("CCMEMORY_MCP_LOG", "/logs/mcp.log")
NEO4J_LOG = os.getenv("CCMEMORY_NEO4J_LOG", "/logs/query.log")

_driver = None


def getDriver():
    global _driver
    if _driver is None:
        uri = os.getenv("CCMEMORY_NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("CCMEMORY_NEO4J_USER", "neo4j")
        password = os.getenv("CCMEMORY_NEO4J_PASSWORD", "ccmemory")
        _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver


def serialize_node(node: dict) -> dict:
    result = {}
    for k, v in node.items():
        if k == "embedding":
            continue
        if hasattr(v, "isoformat"):
            result[k] = v.isoformat()
        elif hasattr(v, "to_native"):
            result[k] = str(v.to_native())
        else:
            result[k] = v
    return result


@app.route("/")
def index():
    project = request.args.get("project", "")
    team = request.args.get("team", "").lower() == "true"
    return render_template("dashboard.html", project=project, team=team)


@app.route("/api/metrics")
def metrics():
    project = request.args.get("project", "")
    driver = getDriver()

    with driver.session() as session:
        result = session.run(
            """
            OPTIONAL MATCH (d:Decision {project: $project})
            WITH count(d) as total_decisions,
                 sum(CASE WHEN d.status = 'curated' THEN 1 ELSE 0 END) as curated
            OPTIONAL MATCH (c:Correction {project: $project})
            WITH total_decisions, curated, count(c) as total_corrections
            OPTIONAL MATCH (i:Insight {project: $project})
            WITH total_decisions, curated, total_corrections, count(i) as total_insights
            OPTIONAL MATCH (s:Session {project: $project})
            WITH total_decisions, curated, total_corrections, total_insights, count(s) as total_sessions
            OPTIONAL MATCH (f:FailedApproach {project: $project})
            RETURN total_decisions, curated, total_corrections, total_insights,
                   total_sessions, count(f) as total_failed_approaches
            """,
            project=project,
        )
        record = result.single()

        total_decisions = record["total_decisions"]
        total_sessions = record["total_sessions"]
        total_corrections = record["total_corrections"]

        reuse_rate = record["curated"] / total_decisions if total_decisions > 0 else 0
        reexplanation_rate = (
            total_corrections / total_sessions if total_sessions > 0 else 0
        )
        coefficient = 1.0 + (total_decisions * 0.02) + (reuse_rate * 1.0)
        coefficient = min(coefficient, 4.0)

        return jsonify(
            {
                "cognitive_coefficient": coefficient,
                "total_decisions": total_decisions,
                "total_corrections": total_corrections,
                "total_insights": record["total_insights"],
                "total_sessions": total_sessions,
                "total_failed_approaches": record["total_failed_approaches"],
                "decision_reuse_rate": reuse_rate,
                "graph_density": 0.0,
                "reexplanation_rate": reexplanation_rate,
            }
        )


@app.route("/api/recent")
def recent():
    project = request.args.get("project", "")
    limit = int(request.args.get("limit", 20))
    driver = getDriver()

    with driver.session() as session:
        result = session.run(
            """
            MATCH (s:Session {project: $project})-[r]->(n)
            WHERE type(r) IN ['DECIDED', 'CORRECTED', 'REALIZED', 'ASKED', 'TRIED', 'EXCEPTED']
            RETURN n, type(r) as rel_type, s.started_at as session_time
            ORDER BY n.timestamp DESC
            LIMIT $limit
            """,
            project=project,
            limit=limit,
        )

        formatted = []
        for record in result:
            node = record["n"]
            session_time = record["session_time"]
            if hasattr(session_time, "isoformat"):
                session_time = session_time.isoformat()
            formatted.append(
                {
                    "type": record["rel_type"],
                    "data": serialize_node(dict(node)),
                    "session_time": str(session_time) if session_time else "",
                }
            )

        return jsonify(formatted)


@app.route("/api/decisions")
def decisions():
    project = request.args.get("project", "")
    status = request.args.get("status")
    limit = int(request.args.get("limit", 50))
    driver = getDriver()

    with driver.session() as session:
        if status:
            result = session.run(
                """
                MATCH (d:Decision {project: $project, status: $status})
                RETURN d ORDER BY d.timestamp DESC LIMIT $limit
                """,
                project=project,
                status=status,
                limit=limit,
            )
        else:
            result = session.run(
                """
                MATCH (d:Decision {project: $project})
                RETURN d ORDER BY d.timestamp DESC LIMIT $limit
                """,
                project=project,
                limit=limit,
            )
        return jsonify([serialize_node(dict(r["d"])) for r in result])


@app.route("/api/corrections")
def corrections():
    project = request.args.get("project", "")
    limit = int(request.args.get("limit", 50))
    driver = getDriver()

    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Correction {project: $project})
            RETURN c ORDER BY c.timestamp DESC LIMIT $limit
            """,
            project=project,
            limit=limit,
        )
        return jsonify([serialize_node(dict(r["c"])) for r in result])


@app.route("/api/insights")
def insights():
    project = request.args.get("project", "")
    category = request.args.get("category")
    limit = int(request.args.get("limit", 50))
    driver = getDriver()

    with driver.session() as session:
        if category:
            result = session.run(
                """
                MATCH (i:Insight {project: $project, category: $category})
                RETURN i ORDER BY i.timestamp DESC LIMIT $limit
                """,
                project=project,
                category=category,
                limit=limit,
            )
        else:
            result = session.run(
                """
                MATCH (i:Insight {project: $project})
                RETURN i ORDER BY i.timestamp DESC LIMIT $limit
                """,
                project=project,
                limit=limit,
            )
        return jsonify([serialize_node(dict(r["i"])) for r in result])


@app.route("/api/failed-approaches")
def failed_approaches():
    project = request.args.get("project", "")
    limit = int(request.args.get("limit", 50))
    driver = getDriver()

    with driver.session() as session:
        result = session.run(
            """
            MATCH (f:FailedApproach {project: $project})
            RETURN f ORDER BY f.timestamp DESC LIMIT $limit
            """,
            project=project,
            limit=limit,
        )
        return jsonify([serialize_node(dict(r["f"])) for r in result])


@app.route("/api/sessions")
def sessions():
    project = request.args.get("project", "")
    limit = int(request.args.get("limit", 50))
    driver = getDriver()

    with driver.session() as session:
        result = session.run(
            """
            MATCH (s:Session {project: $project})
            RETURN s ORDER BY s.started_at DESC LIMIT $limit
            """,
            project=project,
            limit=limit,
        )
        return jsonify([serialize_node(dict(r["s"])) for r in result])


@app.route("/api/clear", methods=["DELETE"])
def clear_database():
    project = request.args.get("project", "")
    if not project:
        return jsonify({"error": "Project name required"}), 400

    driver = getDriver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (n)
            WHERE n.project = $project
            DETACH DELETE n
            RETURN count(n) as deleted
            """,
            project=project,
        )
        record = result.single()
        return jsonify({"deleted": record["deleted"] if record else 0})


@app.route("/api/import", methods=["POST"])
def import_conversations():
    import requests

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.endswith(".zip"):
        return jsonify({"error": "Must upload a .zip file"}), 400

    project = request.form.get("project", "")
    if not project:
        return jsonify({"error": "Project name required"}), 400

    mcp_url = os.getenv("CCMEMORY_MCP_URL", "http://mcp:8766")
    stats = {
        "files_found": 0,
        "files_skipped": 0,
        "processed": 0,
        "detections": 0,
    }

    try:
        zip_data = io.BytesIO(file.read())
        conversations = []

        with zipfile.ZipFile(zip_data, "r") as zf:
            jsonl_files = [n for n in zf.namelist() if n.endswith(".jsonl")]
            stats["files_found"] = len(jsonl_files)

            for name in jsonl_files:
                content = zf.read(name).decode("utf-8", errors="ignore")

                size = len(content)
                if size < 5000 or size > 500000:
                    stats["files_skipped"] += 1
                    continue

                text_chars = sum(
                    1 for c in content[:50000] if c.isalpha() or c.isspace()
                )
                if len(content) > 0 and text_chars / min(len(content), 50000) < 0.3:
                    stats["files_skipped"] += 1
                    continue

                stem = name.rsplit("/", 1)[-1].replace(".jsonl", "")
                conversations.append({"session_id": stem, "content": content})

        if conversations:
            resp = requests.post(
                f"{mcp_url}/api/bulk-import",
                json={"project": project, "conversations": conversations},
                timeout=600,
            )
            if resp.ok:
                result = resp.json()
                stats["processed"] = result.get("processed", 0)
                stats["detections"] = result.get("detections", 0)
                stats["files_skipped"] += result.get("skipped", 0)
            else:
                return jsonify({"error": f"MCP server error: {resp.status_code}"}), 500

    except zipfile.BadZipFile:
        return jsonify({"error": "Invalid zip file"}), 400
    except requests.RequestException as e:
        return jsonify({"error": f"MCP connection failed: {e}"}), 500

    return jsonify(stats)


@app.route("/api/search")
def search():
    project = request.args.get("project", "")
    query = request.args.get("q", "")
    limit = int(request.args.get("limit", 10))

    if not query:
        return jsonify({"error": "Query parameter 'q' required"}), 400

    driver = getDriver()
    results = {
        "decisions": [],
        "corrections": [],
        "insights": [],
        "failed_approaches": [],
    }

    with driver.session() as session:
        # Search decisions
        r = session.run(
            """
            CALL db.index.fulltext.queryNodes('decision_search', $query)
            YIELD node, score
            WHERE node.project = $project
            RETURN node, score LIMIT $limit
            """,
            query=query,
            project=project,
            limit=limit,
        )
        results["decisions"] = [
            (serialize_node(dict(rec["node"])), rec["score"]) for rec in r
        ]

        # Search corrections
        r = session.run(
            """
            CALL db.index.fulltext.queryNodes('correction_search', $query)
            YIELD node, score
            WHERE node.project = $project
            RETURN node, score LIMIT $limit
            """,
            query=query,
            project=project,
            limit=limit,
        )
        results["corrections"] = [
            (serialize_node(dict(rec["node"])), rec["score"]) for rec in r
        ]

        # Search insights
        r = session.run(
            """
            CALL db.index.fulltext.queryNodes('insight_search', $query)
            YIELD node, score
            WHERE node.project = $project
            RETURN node, score LIMIT $limit
            """,
            query=query,
            project=project,
            limit=limit,
        )
        results["insights"] = [
            (serialize_node(dict(rec["node"])), rec["score"]) for rec in r
        ]

        # Search failed approaches
        r = session.run(
            """
            CALL db.index.fulltext.queryNodes('failedapproach_search', $query)
            YIELD node, score
            WHERE node.project = $project
            RETURN node, score LIMIT $limit
            """,
            query=query,
            project=project,
            limit=limit,
        )
        results["failed_approaches"] = [
            (serialize_node(dict(rec["node"])), rec["score"]) for rec in r
        ]

    return jsonify(results)


def wsgi_app(environ, start_response):
    """WSGI app wrapper that handles WebSocket connections."""
    req_path = environ.get("PATH_INFO", "")
    ws = environ.get("wsgi.websocket")

    if req_path == "/ws/logs" and ws:
        handle_logs_websocket(ws)
        return []

    return app(environ, start_response)


def handle_logs_websocket(ws):
    """Handle WebSocket log streaming."""
    log_files = [MCP_LOG, NEO4J_LOG]
    positions = {f: 0 for f in log_files}

    # Send last 50 lines from MCP log on connect
    if os.path.exists(MCP_LOG):
        try:
            with open(MCP_LOG, "r") as f:
                lines = f.readlines()
                for line in lines[-50:]:
                    line = line.strip()
                    if line:
                        ws.send(line)
                positions[MCP_LOG] = f.tell()
        except (IOError, OSError):
            pass

    for log_file in log_files:
        if os.path.exists(log_file) and log_file not in positions:
            positions[log_file] = os.path.getsize(log_file)

    try:
        while not ws.closed:
            for log_file in log_files:
                if not os.path.exists(log_file):
                    continue
                try:
                    with open(log_file, "r") as f:
                        f.seek(positions[log_file])
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            if log_file == MCP_LOG:
                                ws.send(line)
                            else:
                                ws.send(json.dumps({"cat": "neo4j", "raw": line}))
                        positions[log_file] = f.tell()
                except (IOError, OSError):
                    pass
            time.sleep(0.5)
    except WebSocketError:
        pass


def main():
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    port = int(os.getenv("CCMEMORY_DASHBOARD_PORT", 8765))
    server = pywsgi.WSGIServer(
        ("0.0.0.0", port), wsgi_app, handler_class=WebSocketHandler
    )
    print(f"Dashboard running on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
