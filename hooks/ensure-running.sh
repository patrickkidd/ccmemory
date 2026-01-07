#!/bin/bash
# Ensure ccmemory containers are running before tool use
# Called by PreToolUse hook - manages Docker lifecycle and API key config

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/activity_log.sh"

LOG_FILE="$HOME/.ccmemory/ensure-running.log"
mkdir -p "$HOME/.ccmemory"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

HOOK_NAME="ensure_running"
hookStart "$HOOK_NAME"

log "=== ensure-running.sh started ==="

CONFIG_DIR="$HOME/.ccmemory"
CONFIG_FILE="$CONFIG_DIR/config.json"
OLLAMA_CONTAINER="ccmemory-ollama"
NEO4J_CONTAINER="ccmemory-neo4j"
MCP_CONTAINER="ccmemory-mcp"

check_docker() {
    if ! command -v docker &> /dev/null; then
        activityLogError "hook:$HOOK_NAME" "Docker not found"
        echo "Docker not found. Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    if ! docker info &> /dev/null; then
        activityLogError "hook:$HOOK_NAME" "Docker daemon not running"
        echo "Docker daemon not running. Please start Docker."
        exit 1
    fi
    activityLogDebug "hook:$HOOK_NAME" "Docker OK"
}

load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        activityLogDebug "hook:$HOOK_NAME" "Loading config from $CONFIG_FILE"
        ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-$(jq -r '.anthropic_api_key // empty' "$CONFIG_FILE" 2>/dev/null || true)}"
        OPENAI_API_KEY="${OPENAI_API_KEY:-$(jq -r '.openai_api_key // empty' "$CONFIG_FILE" 2>/dev/null || true)}"
        GOOGLE_API_KEY="${GOOGLE_API_KEY:-$(jq -r '.google_api_key // empty' "$CONFIG_FILE" 2>/dev/null || true)}"
    fi
}

has_llm_key() {
    [ -n "$ANTHROPIC_API_KEY" ] || [ -n "$OPENAI_API_KEY" ] || [ -n "$GOOGLE_API_KEY" ] || [ -n "$GEMINI_API_KEY" ]
}

prompt_keys() {
    log "prompt_keys: ANTHROPIC='${ANTHROPIC_API_KEY:+set}' OPENAI='${OPENAI_API_KEY:+set}' GOOGLE='${GOOGLE_API_KEY:+set}'"
    if ! has_llm_key; then
        log "prompt_keys: no LLM key found, prompting"
        activityLogError "hook:$HOOK_NAME" "No LLM API key configured"
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
    activityLogDebug "hook:$HOOK_NAME" "LLM API key found"
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
    activityLogDebug "hook:$HOOK_NAME" "Config saved"
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
    activityLogDebug "hook:$HOOK_NAME" "Waiting for MCP health (max ${max_wait}s)..."
    while [ $waited -lt $max_wait ]; do
        if curl -s http://localhost:8766/health > /dev/null 2>&1; then
            activityLogInfo "hook:$HOOK_NAME" "MCP healthy after ${waited}s"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    activityLogError "hook:$HOOK_NAME" "MCP failed to start after ${max_wait}s"
    echo "MCP server failed to start after ${max_wait}s"
    exit 1
}

main() {
    log "Checking if MCP is already responding..."
    activityLogDebug "hook:$HOOK_NAME" "Checking MCP health..."
    # Quick check - if MCP is already responding, we're done
    if curl -s http://localhost:8766/health > /dev/null 2>&1; then
        log "MCP already healthy, exiting"
        activityLogInfo "hook:$HOOK_NAME" "MCP already healthy"
        hookEnd "$HOOK_NAME"
        exit 0
    fi

    log "MCP not responding, checking docker..."
    activityLogInfo "hook:$HOOK_NAME" "MCP not responding, starting containers..."
    check_docker
    log "Docker OK, loading config..."
    load_config
    log "ANTHROPIC_API_KEY set: $([ -n \"$ANTHROPIC_API_KEY\" ] && echo 'yes' || echo 'no')"
    prompt_keys
    log "prompt_keys passed"
    save_config
    log "save_config done"

    # Find project root (where docker-compose.yml is)
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

    if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        log "docker-compose.yml not found at $PROJECT_ROOT"
        activityLogError "hook:$HOOK_NAME" "docker-compose.yml not found"
        echo "Error: docker-compose.yml not found. Please run from ccmemory directory."
        exit 1
    fi

    log "Starting containers via docker compose..."
    activityLogInfo "hook:$HOOK_NAME" "Starting docker compose..."
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
    activityLogDebug "hook:$HOOK_NAME" "Checking embedding model..."
    if ! docker exec "$OLLAMA_CONTAINER" ollama list 2>/dev/null | grep -q "all-minilm"; then
        log "Pulling all-minilm model..."
        activityLogInfo "hook:$HOOK_NAME" "Pulling all-minilm model..."
        echo "Pulling embedding model (first time only)..."
        docker exec "$OLLAMA_CONTAINER" ollama pull all-minilm 2>&1 | tail -1
    fi

    wait_for_mcp
    log "MCP started"

    log "=== ensure-running.sh completed ==="
    hookEnd "$HOOK_NAME"
}

main
