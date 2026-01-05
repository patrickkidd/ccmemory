#!/bin/bash
# Stop ccmemory services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Stopping ccmemory..."

cd "$ROOT_DIR/docker"
docker-compose down

echo "ccmemory stopped."
