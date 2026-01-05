"""Flask dashboard for ccmemory."""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server', 'src'))

from flask import Flask, render_template, jsonify, request
from ccmemory.graph import getClient

app = Flask(__name__)


def serialize_node(node: dict) -> dict:
    """Convert Neo4j node to JSON-serializable dict."""
    result = {}
    for k, v in node.items():
        if k == 'embedding':
            continue  # Skip large embedding arrays
        if hasattr(v, 'isoformat'):
            result[k] = v.isoformat()
        elif hasattr(v, 'to_native'):
            result[k] = str(v.to_native())
        else:
            result[k] = v
    return result


@app.route("/")
def index():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    team = request.args.get("team", "").lower() == "true"
    return render_template("dashboard.html", project=project, team=team)


@app.route("/api/metrics")
def metrics():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    client = getClient()
    return jsonify(client.getAllMetrics(project))


@app.route("/api/recent")
def recent():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    limit = int(request.args.get("limit", 20))
    client = getClient()
    results = client.queryRecent(project, limit=limit)

    formatted = []
    for item in results:
        node = item.get("n", {})
        if node:
            session_time = item.get("session_time", "")
            if hasattr(session_time, 'isoformat'):
                session_time = session_time.isoformat()
            formatted.append({
                "type": item.get("rel_type", ""),
                "data": serialize_node(dict(node)),
                "session_time": str(session_time)
            })

    return jsonify(formatted)


@app.route("/api/decisions")
def decisions():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    status = request.args.get("status")
    limit = int(request.args.get("limit", 50))

    client = getClient()
    driver = client.driver

    with driver.session() as session:
        if status:
            result = session.run(
                """
                MATCH (d:Decision {project: $project, status: $status})
                RETURN d ORDER BY d.timestamp DESC LIMIT $limit
                """,
                project=project, status=status, limit=limit
            )
        else:
            result = session.run(
                """
                MATCH (d:Decision {project: $project})
                RETURN d ORDER BY d.timestamp DESC LIMIT $limit
                """,
                project=project, limit=limit
            )
        return jsonify([serialize_node(dict(r["d"])) for r in result])


@app.route("/api/corrections")
def corrections():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    limit = int(request.args.get("limit", 50))

    client = getClient()
    driver = client.driver

    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Correction {project: $project})
            RETURN c ORDER BY c.timestamp DESC LIMIT $limit
            """,
            project=project, limit=limit
        )
        return jsonify([serialize_node(dict(r["c"])) for r in result])


@app.route("/api/insights")
def insights():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    category = request.args.get("category")
    limit = int(request.args.get("limit", 50))

    client = getClient()
    driver = client.driver

    with driver.session() as session:
        if category:
            result = session.run(
                """
                MATCH (i:Insight {project: $project, category: $category})
                RETURN i ORDER BY i.timestamp DESC LIMIT $limit
                """,
                project=project, category=category, limit=limit
            )
        else:
            result = session.run(
                """
                MATCH (i:Insight {project: $project})
                RETURN i ORDER BY i.timestamp DESC LIMIT $limit
                """,
                project=project, limit=limit
            )
        return jsonify([serialize_node(dict(r["i"])) for r in result])


@app.route("/api/failed-approaches")
def failed_approaches():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    limit = int(request.args.get("limit", 50))

    client = getClient()
    results = client.queryFailedApproaches(project, limit=limit)
    return jsonify(results)


@app.route("/api/sessions")
def sessions():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    limit = int(request.args.get("limit", 50))

    client = getClient()
    driver = client.driver

    with driver.session() as session:
        result = session.run(
            """
            MATCH (s:Session {project: $project})
            RETURN s ORDER BY s.started_at DESC LIMIT $limit
            """,
            project=project, limit=limit
        )
        return jsonify([serialize_node(dict(r["s"])) for r in result])


@app.route("/api/search")
def search():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    query = request.args.get("q", "")
    limit = int(request.args.get("limit", 10))

    if not query:
        return jsonify({"error": "Query parameter 'q' required"}), 400

    client = getClient()
    results = client.searchPrecedent(query, project, limit=limit)
    # Serialize the results to handle Neo4j DateTime objects
    serialized = {}
    for category, items in results.items():
        serialized[category] = [
            (serialize_node(item[0]), item[1]) for item in items
        ]
    return jsonify(serialized)


def main():
    """Run the dashboard."""
    port = int(os.getenv("CCMEMORY_DASHBOARD_PORT", 8765))
    debug = os.getenv("CCMEMORY_DEBUG", "").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
