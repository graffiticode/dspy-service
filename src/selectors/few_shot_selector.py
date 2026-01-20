"""Few-shot example selector.

This module will contain DSPy-based few-shot selection logic in Phase 4.
For now, it provides a simple pass-through implementation.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.api.models import RetrievedChunk


def select_few_shot_examples(
    retrieved_chunks: list["RetrievedChunk"],
    max_examples: int = 3,
) -> list["RetrievedChunk"]:
    """
    Select the best few-shot examples from retrieved chunks.

    Currently uses a simple top-k selection based on similarity scores.
    In Phase 4, this will be replaced with DSPy-based intelligent selection.

    Args:
        retrieved_chunks: List of retrieved chunks with similarity scores
        max_examples: Maximum number of examples to return

    Returns:
        Selected chunks for use as few-shot examples
    """
    # Sort by combined score (if available) or similarity
    def get_score(chunk: "RetrievedChunk") -> float:
        if chunk.combined_score is not None:
            return chunk.combined_score
        if chunk.similarity is not None:
            return chunk.similarity
        return 0.0

    sorted_chunks = sorted(retrieved_chunks, key=get_score, reverse=True)

    return sorted_chunks[:max_examples]
