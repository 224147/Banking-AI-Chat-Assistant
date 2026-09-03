"""Lightweight lexical-overlap reranker. Offloaded to a thread since scoring many
candidates is CPU-bound. Swap in a cross-encoder model here for production use."""
import asyncio
import re

_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


def _overlap_score(query: str, text: str) -> float:
    query_tokens = set(_TOKEN_RE.findall(query.lower()))
    text_tokens = set(_TOKEN_RE.findall(text.lower()))
    if not query_tokens or not text_tokens:
        return 0.0
    return len(query_tokens & text_tokens) / len(query_tokens)


async def rerank(query: str, candidates: list[dict]) -> list[dict]:
    return await asyncio.to_thread(_rerank_sync, query, candidates)


def _rerank_sync(query: str, candidates: list[dict]) -> list[dict]:
    reranked = []
    for candidate in candidates:
        lexical = _overlap_score(query, candidate["text"])
        combined_score = 0.6 * candidate["score"] + 0.4 * lexical
        reranked.append({**candidate, "score": combined_score})
    return sorted(reranked, key=lambda c: c["score"], reverse=True)
