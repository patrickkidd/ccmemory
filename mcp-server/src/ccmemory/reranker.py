"""Claude-based reranking for semantic search results."""

import json

from anthropic import AsyncAnthropic

RERANK_MODEL = "claude-sonnet-4-20250514"

_client = None


def _getClient():
    global _client
    if _client is None:
        _client = AsyncAnthropic()
    return _client


RERANK_PROMPT = """Rank these items by relevance to the query. Return the indices of the {limit} most relevant items, ordered by relevance (most relevant first).

Query: {query}

Items:
{items}

Return only JSON: {{"indices": [0, 3, 1, ...]}}"""


async def rerank(query: str, candidates: list[dict], limit: int = 5) -> list[dict]:
    """Rerank candidates by relevance using Claude.

    Args:
        query: The search query
        candidates: List of candidate items with 'data' and 'score' keys
        limit: Number of top results to return

    Returns:
        Reranked list of candidates
    """
    if len(candidates) <= limit:
        return candidates

    items_text = "\n".join(f"[{i}] {_formatCandidate(c)}" for i, c in enumerate(candidates))

    prompt = RERANK_PROMPT.format(limit=limit, query=query, items=items_text)

    client = _getClient()
    response = await client.messages.create(
        model=RERANK_MODEL, max_tokens=200, messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text

    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(text[start:end])
            indices = result.get("indices", [])
            reranked = []
            for idx in indices[:limit]:
                if 0 <= idx < len(candidates):
                    reranked.append(candidates[idx])
            return reranked
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    return candidates[:limit]


def _formatCandidate(candidate: dict) -> str:
    """Format candidate data for the prompt."""
    data = candidate.get("data", {})
    parts = []

    if "description" in data:
        parts.append(data["description"][:200])
    if "rationale" in data:
        parts.append(f"Rationale: {data['rationale'][:100]}")
    if "wrong_belief" in data:
        parts.append(f"Wrong: {data['wrong_belief'][:100]}")
    if "right_belief" in data:
        parts.append(f"Right: {data['right_belief'][:100]}")
    if "summary" in data:
        parts.append(data["summary"][:200])

    return " | ".join(parts) if parts else str(data)[:300]
