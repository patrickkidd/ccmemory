#!/bin/bash
# Start ccmemory services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting ccmemory..."

# Start Neo4j
echo "Starting Neo4j..."
cd "$ROOT_DIR/docker"
docker-compose up -d

# Wait for Neo4j
echo "Waiting for Neo4j to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo "Neo4j is ready!"
        break
    fi
    sleep 1
done

echo ""
echo "ccmemory started!"
echo "  Neo4j Browser: http://localhost:7474"
echo "  Neo4j Bolt:    bolt://localhost:7687"
echo ""
echo "To start the dashboard: ccmemory dashboard"
