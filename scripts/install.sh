#!/bin/bash
# Install ccmemory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Installing ccmemory..."

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is required but not installed."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is required but not installed."
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Install Python package
echo "Installing Python package..."
cd "$ROOT_DIR/mcp-server"
pip install -e ".[dev]"

# Start Neo4j
echo "Starting Neo4j..."
cd "$ROOT_DIR/docker"
docker-compose up -d

# Wait for Neo4j to be ready
echo "Waiting for Neo4j to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo "Neo4j is ready!"
        break
    fi
    sleep 1
done

# Initialize schema
echo "Initializing schema..."
python3 -c "
import sys
sys.path.insert(0, '$ROOT_DIR/mcp-server/src')
from ccmemory.graph import getClient

client = getClient()
with open('$ROOT_DIR/docker/init.cypher', 'r') as f:
    statements = f.read().split(';')
    for stmt in statements:
        stmt = stmt.strip()
        if stmt and not stmt.startswith('//'):
            try:
                with client.driver.session() as session:
                    session.run(stmt)
            except Exception as e:
                if 'already exists' not in str(e).lower():
                    print(f'Warning: {e}')
print('Schema initialized!')
"

echo ""
echo "ccmemory installed successfully!"
echo ""
echo "Environment variables to set:"
echo "  export VOYAGE_API_KEY='your-voyage-api-key'"
echo ""
echo "Commands:"
echo "  ccmemory status    - Check connection"
echo "  ccmemory stats     - Show metrics"
echo "  ccmemory dashboard - Start web dashboard"
