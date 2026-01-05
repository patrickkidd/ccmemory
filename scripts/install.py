#!/usr/bin/env python3

import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent


def check(cmd: str, name: str, hint: str | None = None) -> bool:
    if shutil.which(cmd):
        return True
    print(f"Error: {name} is required but not installed.")
    if hint:
        print(f"Install with: {hint}")
    return False


def run(cmd: list[str], cwd: Path | None = None) -> bool:
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode == 0


def main() -> int:
    print("Installing ccmemory...")

    # Check dependencies
    if not check("docker", "Docker"):
        return 1
    if not check("docker-compose", "docker-compose"):
        return 1
    if not check("python3", "Python 3"):
        return 1
    if not check("uv", "uv", "curl -LsSf https://astral.sh/uv/install.sh | sh"):
        return 1

    # Install Python package
    print("Installing Python package...")
    if not run(["uv", "pip", "install", "-e", ".[dev]"], cwd=ROOT_DIR / "mcp-server"):
        print("Error: Failed to install Python package")
        return 1

    # Start Neo4j
    print("Starting Neo4j...")
    if not run(["docker-compose", "up", "-d"], cwd=ROOT_DIR):
        print("Error: Failed to start Neo4j")
        return 1

    # Wait for Neo4j
    print("Waiting for Neo4j to be ready...")
    import urllib.request
    import urllib.error
    for _ in range(30):
        try:
            urllib.request.urlopen("http://localhost:7474", timeout=1)
            print("Neo4j is ready!")
            break
        except (urllib.error.URLError, TimeoutError):
            time.sleep(1)

    # Initialize schema
    print("Initializing schema...")
    sys.path.insert(0, str(ROOT_DIR / "mcp-server" / "src"))
    from ccmemory.graph import getClient

    client = getClient()
    cypher = (ROOT_DIR / "init.cypher").read_text()
    for stmt in cypher.split(";"):
        stmt = stmt.strip()
        if stmt and not stmt.startswith("//"):
            with client.driver.session() as session:
                session.run(stmt)
    print("Schema initialized!")

    print()
    print("ccmemory installed successfully!")
    print()
    print("Environment variables to set:")
    print("  export VOYAGE_API_KEY='your-voyage-api-key'")
    print()
    print("Commands:")
    print("  ccmemory status    - Check connection")
    print("  ccmemory stats     - Show metrics")
    print("  ccmemory dashboard - Start web dashboard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
