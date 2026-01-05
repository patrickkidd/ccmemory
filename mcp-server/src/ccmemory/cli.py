"""CLI commands for ccmemory."""

import os
import subprocess
import sys

import click


@click.group()
def main():
    """ccmemory: Context graph for persistent memory across Claude Code sessions."""
    pass


@main.command()
def start():
    """Start Neo4j and the dashboard."""
    docker_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'docker')

    click.echo("Starting Neo4j...")
    result = subprocess.run(
        ['docker-compose', 'up', '-d'],
        cwd=docker_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        click.echo(f"Failed to start Neo4j: {result.stderr}", err=True)
        sys.exit(1)

    click.echo("Neo4j started on bolt://localhost:7687")
    click.echo("Neo4j Browser available at http://localhost:7474")

    click.echo("\nWaiting for Neo4j to be ready...")
    import time
    for _ in range(30):
        try:
            from .graph import getClient
            client = getClient()
            client.driver.verify_connectivity()
            click.echo("Neo4j is ready!")
            break
        except Exception:
            time.sleep(1)
    else:
        click.echo("Warning: Neo4j may not be fully ready yet", err=True)

    click.echo("\nInitializing schema...")
    init_cypher = os.path.join(docker_dir, 'init.cypher')
    if os.path.exists(init_cypher):
        try:
            from .graph import getClient
            client = getClient()
            with open(init_cypher, 'r') as f:
                statements = f.read().split(';')
                for stmt in statements:
                    stmt = stmt.strip()
                    if stmt and not stmt.startswith('//'):
                        try:
                            with client.driver.session() as session:
                                session.run(stmt)
                        except Exception as e:
                            if 'already exists' not in str(e).lower():
                                click.echo(f"Warning: {e}", err=True)
            click.echo("Schema initialized!")
        except Exception as e:
            click.echo(f"Warning: Could not initialize schema: {e}", err=True)


@main.command()
def stop():
    """Stop Neo4j."""
    docker_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'docker')

    click.echo("Stopping Neo4j...")
    result = subprocess.run(
        ['docker-compose', 'down'],
        cwd=docker_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        click.echo(f"Failed to stop Neo4j: {result.stderr}", err=True)
        sys.exit(1)

    click.echo("Neo4j stopped")


@main.command()
def status():
    """Check Neo4j connection status."""
    try:
        from .graph import getClient
        client = getClient()
        client.driver.verify_connectivity()
        click.echo("Neo4j: Connected")

        project = os.path.basename(os.getcwd())
        metrics = client.getAllMetrics(project)
        click.echo(f"\nProject: {project}")
        click.echo(f"Cognitive Coefficient: {metrics['cognitive_coefficient']:.2f}x")
        click.echo(f"Total Decisions: {metrics['total_decisions']}")
        click.echo(f"Total Corrections: {metrics['total_corrections']}")
        click.echo(f"Total Sessions: {metrics['total_sessions']}")
        click.echo(f"Total Insights: {metrics['total_insights']}")
        click.echo(f"Decision Reuse Rate: {metrics['decision_reuse_rate']*100:.1f}%")
        click.echo(f"Graph Density: {metrics['graph_density']:.2f}")

    except Exception as e:
        click.echo(f"Neo4j: Not connected ({e})", err=True)
        sys.exit(1)


@main.command()
@click.option('--port', default=8765, help='Port to run dashboard on')
@click.option('--debug', is_flag=True, help='Run in debug mode')
def dashboard(port, debug):
    """Start the web dashboard."""
    os.environ['CCMEMORY_DASHBOARD_PORT'] = str(port)
    if debug:
        os.environ['CCMEMORY_DEBUG'] = 'true'

    click.echo(f"Starting dashboard on http://localhost:{port}")

    # Dashboard is at project root level (ccmemory/dashboard)
    # This file is at: ccmemory/mcp-server/src/ccmemory/cli.py
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    sys.path.insert(0, project_root)
    from dashboard.app import app
    app.run(host='0.0.0.0', port=port, debug=debug)


@main.command()
@click.argument('url')
def cache(url):
    """Cache a URL to the reference knowledge tree."""
    from .tools.reference import _cacheUrlImpl

    project_root = os.getcwd()
    result = _cacheUrlImpl(url, project_root)
    click.echo(f"Cached: {result['file']}")
    click.echo(f"Title: {result['title']}")
    click.echo(f"Characters: {result['chars']}")


@main.command('cache-pdf')
@click.argument('path')
def cache_pdf(path):
    """Cache a PDF to the reference knowledge tree."""
    from .tools.reference import _cachePdfImpl

    project_root = os.getcwd()
    result = _cachePdfImpl(path, project_root)
    click.echo(f"Cached: {result['file']}")
    click.echo(f"Pages: {result['pages']}")


@main.command()
def index():
    """Rebuild the reference knowledge index."""
    from .tools.reference import _indexAll

    project_root = os.getcwd()
    count = _indexAll(project_root)
    click.echo(f"Indexed {count} chunks")


@main.command()
@click.argument('query')
@click.option('--limit', default=10, help='Maximum results')
def search(query, limit):
    """Search the context graph."""
    from .graph import getClient

    project = os.path.basename(os.getcwd())
    client = getClient()
    results = client.searchPrecedent(query, project, limit=limit)

    for category, items in results.items():
        if items:
            click.echo(f"\n{category.upper()}")
            click.echo("-" * 40)
            for item, score in items:
                desc = item.get('description') or item.get('summary') or item.get('right_belief') or str(item)[:80]
                click.echo(f"  [{score:.2f}] {desc}")


@main.command()
@click.option('--days', default=30, help='Days threshold for stale decisions')
def stale(days):
    """Show stale developmental decisions."""
    from .graph import getClient

    project = os.path.basename(os.getcwd())
    client = getClient()
    results = client.queryStaleDecisions(project, days=days)

    if not results:
        click.echo("No stale decisions found")
        return

    click.echo(f"Stale decisions (>{days} days old):")
    for d in results:
        click.echo(f"  - {d.get('description', 'No description')[:60]}")
        if d.get('revisit_trigger'):
            click.echo(f"    Revisit trigger: {d['revisit_trigger']}")


@main.command()
@click.option('--branch', help='Only promote decisions from this branch')
def promote(branch):
    """Promote developmental decisions to curated status."""
    from .graph import getClient

    project = os.path.basename(os.getcwd())
    client = getClient()
    client.promoteDecisions(project, branch=branch)

    if branch:
        click.echo(f"Promoted decisions from branch: {branch}")
    else:
        click.echo("Promoted all developmental decisions")


@main.command()
@click.option('--format', 'fmt', type=click.Choice(['text', 'json']), default='text')
def stats(fmt):
    """Show context graph statistics."""
    from .graph import getClient
    import json as json_module

    project = os.path.basename(os.getcwd())
    client = getClient()
    metrics = client.getAllMetrics(project)

    if fmt == 'json':
        click.echo(json_module.dumps(metrics, indent=2))
    else:
        click.echo(f"Project: {project}")
        click.echo(f"\nCognitive Coefficient: {metrics['cognitive_coefficient']:.2f}x")
        click.echo(f"\nGraph Contents:")
        click.echo(f"  Sessions: {metrics['total_sessions']}")
        click.echo(f"  Decisions: {metrics['total_decisions']}")
        click.echo(f"  Corrections: {metrics['total_corrections']}")
        click.echo(f"  Insights: {metrics['total_insights']}")
        click.echo(f"  Failed Approaches: {metrics['total_failed_approaches']}")
        click.echo(f"\nQuality Metrics:")
        click.echo(f"  Re-explanation Rate: {metrics['reexplanation_rate']*100:.1f}%")
        click.echo(f"  Decision Reuse Rate: {metrics['decision_reuse_rate']*100:.1f}%")
        click.echo(f"  Graph Density: {metrics['graph_density']:.2f}")


if __name__ == '__main__':
    main()
