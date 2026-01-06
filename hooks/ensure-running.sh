#!/bin/bash
# Ensure ccmemory containers are running before tool use
# Called by PreToolUse hook - manages Docker lifecycle and API key config

set -e

LOG_FILE="$HOME/.ccmemory/ensure-running.log"
mkdir -p "$HOME/.ccmemory"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log "=== ensure-running.sh started ==="

CONFIG_DIR="$HOME/.ccmemory"
CONFIG_FILE="$CONFIG_DIR/config.json"
OLLAMA_CONTAINER="ccmemory-ollama"
NEO4J_CONTAINER="ccmemory-neo4j"
MCP_CONTAINER="ccmemory-mcp"

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
        ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-$(grep -o '"anthropic_api_key":"[^"]*"' "$CONFIG_FILE" 2>/dev/null | cut -d'"' -f4 || true)}"
        OPENAI_API_KEY="${OPENAI_API_KEY:-$(grep -o '"openai_api_key":"[^"]*"' "$CONFIG_FILE" 2>/dev/null | cut -d'"' -f4 || true)}"
        GOOGLE_API_KEY="${GOOGLE_API_KEY:-$(grep -o '"google_api_key":"[^"]*"' "$CONFIG_FILE" 2>/dev/null | cut -d'"' -f4 || true)}"
    fi
}

has_llm_key() {
    [ -n "$ANTHROPIC_API_KEY" ] || [ -n "$OPENAI_API_KEY" ] || [ -n "$GOOGLE_API_KEY" ] || [ -n "$GEMINI_API_KEY" ]
}

prompt_keys() {
    log "prompt_keys: ANTHROPIC='${ANTHROPIC_API_KEY:+set}' OPENAI='${OPENAI_API_KEY:+set}' GOOGLE='${GOOGLE_API_KEY:+set}'"
    if ! has_llm_key; then
        log "prompt_keys: no LLM key found, prompting"
        echo ""
        echo "=== ccmemory First-Time Setup ==="
        echo ""
        echo "An LLM API key is required. Set ONE of these environment variables:"
        echo ""
        echo "  ANTHROPIC_API_KEY  - https://console.anthropic.com/settings/keys"
        echo "  OPENAI_API_KEY     - https://platform.openai.com/api-keys"
        echo "  GOOGLE_API_KEY     - https://aistudio.google.com/apikey"
        echo ""
        echo "The key will be stored in ~/.ccmemory/config.json"
        exit 1
    fi
}

save_config() {
    log "save_config: creating $CONFIG_DIR"
    mkdir -p "$CONFIG_DIR"
    log "save_config: writing $CONFIG_FILE"
    cat > "$CONFIG_FILE" << EOF
{
  "anthropic_api_key": "${ANTHROPIC_API_KEY:-}",
  "openai_api_key": "${OPENAI_API_KEY:-}",
  "google_api_key": "${GOOGLE_API_KEY:-${GEMINI_API_KEY:-}}"
}
EOF
    chmod 600 "$CONFIG_FILE"
    log "save_config: done"
}

is_container_running() {
    docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null | grep -q "true"
}

is_container_healthy() {
    status=$(docker inspect -f '{{.State.Health.Status}}' "$1" 2>/dev/null || echo "none")
    [ "$status" = "healthy" ]
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
    log "Checking if MCP is already responding..."
    # Quick check - if MCP is already responding, we're done
    if curl -s http://localhost:8766/health > /dev/null 2>&1; then
        log "MCP already healthy, exiting"
        exit 0
    fi

    log "MCP not responding, checking docker..."
    check_docker
    log "Docker OK, loading config..."
    load_config
    log "ANTHROPIC_API_KEY set: $([ -n \"$ANTHROPIC_API_KEY\" ] && echo 'yes' || echo 'no')"
    prompt_keys
    log "prompt_keys passed"
    save_config
    log "save_config done"

    # Find project root (where docker-compose.yml is)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

    if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        log "docker-compose.yml not found at $PROJECT_ROOT"
        echo "Error: docker-compose.yml not found. Please run from ccmemory directory."
        exit 1
    fi

    log "Starting containers via docker compose..."
    echo "Starting ccmemory containers..."

    # Export API keys for docker compose
    [ -n "$ANTHROPIC_API_KEY" ] && export ANTHROPIC_API_KEY
    [ -n "$OPENAI_API_KEY" ] && export OPENAI_API_KEY
    [ -n "$GOOGLE_API_KEY" ] && export GOOGLE_API_KEY
    [ -n "$GEMINI_API_KEY" ] && export GEMINI_API_KEY

    # Start all services
    cd "$PROJECT_ROOT"
    docker compose up -d 2>&1 | grep -v "^time=" || true

    # Pull embedding model if not present
    log "Ensuring embedding model is available..."
    if ! docker exec "$OLLAMA_CONTAINER" ollama list 2>/dev/null | grep -q "all-minilm"; then
        log "Pulling all-minilm model..."
        echo "Pulling embedding model (first time only)..."
        docker exec "$OLLAMA_CONTAINER" ollama pull all-minilm 2>&1 | tail -1
    fi

    wait_for_mcp
    log "MCP started"

    log "=== ensure-running.sh completed ==="
}

main
