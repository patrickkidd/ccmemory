FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
COPY init.cypher .
COPY src/ src/

RUN uv pip install --system .

ENV CCMEMORY_NEO4J_URI=bolt://neo4j:7687
ENV CCMEMORY_NEO4J_PASSWORD=ccmemory

EXPOSE 8766

CMD ["python", "-m", "ccmemory.server", "--http", "--port", "8766"]
