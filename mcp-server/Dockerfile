FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/patrickkidd/ccmemory"
LABEL org.opencontainers.image.description="ccmemory MCP server - persistent memory for Claude Code"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

COPY pyproject.toml .
COPY init.cypher .
COPY src/ src/

RUN uv pip install --system .

ENV CCMEMORY_NEO4J_URI=bolt://ccmemory-neo4j:7687
ENV CCMEMORY_NEO4J_PASSWORD=ccmemory

EXPOSE 8766

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8766/health || exit 1

CMD ["python", "-m", "ccmemory.server", "--http", "--port", "8766"]
