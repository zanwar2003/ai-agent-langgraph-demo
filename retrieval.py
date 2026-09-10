"""
Lightweight keyword-overlap retrieval over a folder of markdown docs.

No embeddings or external API calls required â this is a deliberately simple, dependency-light
retriever so the agent demo runs out of the box. Swapping it for a real vector-store retriever
(see README) doesn't require changing anything else in the graph.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_WORD_RE = re.compile(r"[a-z0-9']+")

# Common words filtered out so they don't create false-positive overlap between an unrelated
# query and a chunk that merely happens to share function words with it.
_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "i", "you", "he", "she", "it", "we", "they", "my", "your", "his", "her", "its", "our", "their",
    "and", "or", "but", "if", "so", "to", "of", "in", "on", "at", "for", "with", "as", "by",
    "this", "that", "these", "those", "do", "does", "did", "have", "has", "had",
    "what", "why", "how", "when", "where", "who", "which", "should", "would", "could", "can",
}


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower())) - _STOPWORDS


@dataclass
class Chunk:
    source: str
    heading: str
    text: str


def load_chunks(docs_dir: str | Path) -> list[Chunk]:
    """Split each markdown file into chunks on '## ' headings."""
    chunks: list[Chunk] = []
    for path in sorted(Path(docs_dir).glob("*.md")):
        content = path.read_text(encoding="utf-8")
        sections = re.split(r"(?m)^## ", content)
        title_line = sections[0].splitlines()[0].lstrip("# ").strip()
        for section in sections[1:]:
            lines = section.splitlines()
            heading = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            chunks.append(Chunk(source=f"{path.name} ({title_line})", heading=heading, text=body))
    return chunks


def retrieve(query: str, chunks: list[Chunk], top_k: int = 2) -> list[tuple[Chunk, float]]:
    """Score chunks by token overlap with the query and return the top_k highest-scoring."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    scored: list[tuple[Chunk, float]] = []
    for chunk in chunks:
        chunk_tokens = _tokenize(f"{chunk.heading} {chunk.text}")
        if not chunk_tokens:
            continue
        overlap = query_tokens & chunk_tokens
        if not overlap:
            continue
        # Simple normalized overlap score, weighted slightly toward heading matches.
        heading_tokens = _tokenize(chunk.heading)
        heading_bonus = len(query_tokens & heading_tokens) * 0.5
        score = len(overlap) / len(query_tokens) + heading_bonus
        scored.append((chunk, score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]
