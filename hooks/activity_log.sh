#!/bin/bash
# Shared activity logging for ccmemory hooks
# Usage: source activity_log.sh; activityLog "INFO" "component" "message"

INSTANCE_DIR="${PWD}/instance"
mkdir -p "$INSTANCE_DIR"
ACTIVITY_LOG="${CCMEMORY_HOOKS_LOG:-$INSTANCE_DIR/hooks.log}"

activityLog() {
    local level="$1"
    local component="$2"
    local message="$3"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] [$component] $message" >> "$ACTIVITY_LOG"
}

activityLogDebug() {
    activityLog "DEBUG" "$1" "$2"
}

activityLogInfo() {
    activityLog "INFO" "$1" "$2"
}

activityLogError() {
    activityLog "ERROR" "$1" "$2"
}

hookStart() {
    local hook_name="$1"
    HOOK_START_TIME=$(date +%s%N)
    activityLogInfo "hook:$hook_name" "=== HOOK START ==="
}

hookEnd() {
    local hook_name="$1"
    local end_time=$(date +%s%N)
    local duration_ms=$(( (end_time - HOOK_START_TIME) / 1000000 ))
    activityLogInfo "hook:$hook_name" "=== HOOK END (${duration_ms}ms) ==="
}
