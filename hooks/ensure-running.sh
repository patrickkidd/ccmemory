#!/bin/bash
# Ensure ccmemory containers are running before tool use
# Called by PreToolUse hook - manages Docker lifecycle and API key config

set -e

CONFIG_DIR="$HOME/.ccmemory"
CONFIG_FILE="$CONFIG_DIR/config.json"
NETWORK_NAME="ccmemory-net"
NEO4J_CONTAINER="ccmemory-neo4j"
MCP_CONTAINER="ccmemory-mcp"
NEO4J_IMAGE="neo4j:5.15-community"
MCP_IMAGE="ghcr.io/patrickkidd/ccmemory:latest"

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Docker not found. Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    if ! docker info &> /dev/null; then
        echo "Docker daemon not running. Please start Docker."
        exit 1
    fi
}

load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        VOYAGE_API_KEY=$(grep -o '"voyage_api_key":"[^"]*"' "$CONFIG_FILE" 2>/dev/null | cut -d'"' -f4 || true)
        ANTHROPIC_API_KEY=$(grep -o '"anthropic_api_key":"[^"]*"' "$CONFIG_FILE" 2>/dev/null | cut -d'"' -f4 || true)
    fi
    # Fall back to environment
    VOYAGE_API_KEY="${VOYAGE_API_KEY:-$VOYAGE_API_KEY}"
    ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-$ANTHROPIC_API_KEY}"
}

prompt_keys() {
    if [ -z "$VOYAGE_API_KEY" ] || [ -z "$ANTHROPIC_API_KEY" ]; then
        echo ""
        echo "=== ccmemory First-Time Setup ==="
        echo ""
        echo "API keys required for ccmemory. They will be stored in ~/.ccmemory/config.json"
        echo ""

        if [ -z "$VOYAGE_API_KEY" ]; then
            echo "VOYAGE_API_KEY not found."
            echo "Get one at: https://dash.voyageai.com/api-keys"
            echo ""
            echo "Please set VOYAGE_API_KEY environment variable and retry."
            exit 1
        fi

        if [ -z "$ANTHROPIC_API_KEY" ]; then
            echo "ANTHROPIC_API_KEY not found."
            echo "Get one at: https://console.anthropic.com/settings/keys"
            echo ""
            echo "Please set ANTHROPIC_API_KEY environment variable and retry."
            exit 1
        fi
    fi
}

save_config() {
    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_FILE" << EOF
{
  "voyage_api_key": "$VOYAGE_API_KEY",
  "anthropic_api_key": "$ANTHROPIC_API_KEY"
}
EOF
    chmod 600 "$CONFIG_FILE"
}

ensure_network() {
    if ! docker network inspect "$NETWORK_NAME" &> /dev/null; then
        docker network create "$NETWORK_NAME" > /dev/null
    fi
}

is_container_running() {
    docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null | grep -q "true"
}

is_container_healthy() {
    status=$(docker inspect -f '{{.State.Health.Status}}' "$1" 2>/dev/null || echo "none")
    [ "$status" = "healthy" ]
}

start_neo4j() {
    if is_container_running "$NEO4J_CONTAINER"; then
        return 0
    fi

    # Remove stopped container if exists
    docker rm -f "$NEO4J_CONTAINER" 2>/dev/null || true

    docker run -d \
        --name "$NEO4J_CONTAINER" \
        --network "$NETWORK_NAME" \
        -p 7474:7474 \
        -p 7687:7687 \
        -v ccmemory_data:/data \
        -v ccmemory_logs:/logs \
        -e NEO4J_AUTH=neo4j/ccmemory \
        -e NEO4J_PLUGINS='["apoc"]' \
        --health-cmd "wget -q --spider http://localhost:7474 || exit 1" \
        --health-interval 5s \
        --health-timeout 5s \
        --health-retries 12 \
        "$NEO4J_IMAGE" > /dev/null
}

start_mcp() {
    if is_container_running "$MCP_CONTAINER"; then
        return 0
    fi

    # Remove stopped container if exists
    docker rm -f "$MCP_CONTAINER" 2>/dev/null || true

    docker run -d \
        --name "$MCP_CONTAINER" \
        --network "$NETWORK_NAME" \
        -p 8766:8766 \
        -e CCMEMORY_NEO4J_URI=bolt://ccmemory-neo4j:7687 \
        -e CCMEMORY_NEO4J_PASSWORD=ccmemory \
        -e VOYAGE_API_KEY="$VOYAGE_API_KEY" \
        -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
        -e CCMEMORY_USER_ID="${CCMEMORY_USER_ID:-}" \
        "$MCP_IMAGE" > /dev/null
}

wait_for_neo4j() {
    local max_wait=60
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if is_container_healthy "$NEO4J_CONTAINER"; then
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    echo "Neo4j failed to become healthy after ${max_wait}s"
    exit 1
}

wait_for_mcp() {
    local max_wait=30
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if curl -s http://localhost:8766/health > /dev/null 2>&1; then
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    echo "MCP server failed to start after ${max_wait}s"
    exit 1
}

main() {
    # Quick check - if MCP is already responding, we're done
    if curl -s http://localhost:8766/health > /dev/null 2>&1; then
        exit 0
    fi

    check_docker
    load_config
    prompt_keys
    save_config
    ensure_network

    # Start Neo4j if needed
    if ! is_container_running "$NEO4J_CONTAINER"; then
        echo "Starting Neo4j..."
        start_neo4j
        wait_for_neo4j
    fi

    # Start MCP if needed
    if ! is_container_running "$MCP_CONTAINER"; then
        echo "Starting ccmemory MCP server..."
        start_mcp
        wait_for_mcp
    fi
}

main
