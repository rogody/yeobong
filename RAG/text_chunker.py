from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class TextChunk:
    """Represents a chunk of tokens within the source message."""

    ord: int
    token_start: int
    token_end: int
    text: str


def chunk_text(
    text: str,
    chunk_size: int = 250,
    overlap_ratio: float = 0.2,
) -> List[TextChunk]:
    """
    Split text into overlapping chunks based on whitespace-delimited tokens.

    Args:
        text: The original text to split.
        chunk_size: Target number of tokens per chunk.
        overlap_ratio: Fraction of chunk_size shared with the subsequent chunk.

    Returns:
        A list of TextChunk instances capturing the token ranges and text slices.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    if overlap_ratio < 0 or overlap_ratio >= 1:
        raise ValueError("overlap_ratio must be between 0 (inclusive) and 1 (exclusive).")

    tokens = text.split()
    if not tokens:
        return []

    overlap_tokens = int(chunk_size * overlap_ratio)
    # Ensure we move forward at least one token per iteration.
    if overlap_tokens >= chunk_size:
        overlap_tokens = chunk_size - 1
    step = max(1, chunk_size - overlap_tokens)

    chunks: List[TextChunk] = []
    start = 0
    chunk_ord = 1
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_value = " ".join(chunk_tokens)
        chunks.append(
            TextChunk(
                ord=chunk_ord,
                token_start=start,
                token_end=end,
                text=chunk_text_value,
            )
        )
        if end >= len(tokens):
            break
        start += step
        chunk_ord += 1
    return chunks
