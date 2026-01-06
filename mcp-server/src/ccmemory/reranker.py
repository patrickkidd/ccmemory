"""LLM-based reranking for semantic search results."""

from ccmemory.llmprovider import getLlmClient
from ccmemory.detection.schemas import RerankResult


RERANK_PROMPT = """Rank these items by relevance to the query. Return the indices of the {limit} most relevant items, ordered by relevance (most relevant first).

Query: {query}

Items:
{items}"""


async def rerank(query: str, candidates: list[dict], limit: int = 5) -> list[dict]:
    """Rerank candidates by relevance using LLM.

    Args:
        query: The search query
        candidates: List of candidate items with 'data' and 'score' keys
        limit: Number of top results to return

    Returns:
        Reranked list of candidates
    """
    if len(candidates) <= limit:
        return candidates

    items_text = "\n".join(
        f"[{i}] {_formatCandidate(c)}" for i, c in enumerate(candidates)
    )
    prompt = RERANK_PROMPT.format(limit=limit, query=query, items=items_text)

    client = getLlmClient()
    result = await client.complete(prompt, RerankResult, maxTokens=200)

    reranked = []
    for idx in result.indices[:limit]:
        if 0 <= idx < len(candidates):
            reranked.append(candidates[idx])
    return reranked if reranked else candidates[:limit]


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
