from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be between 0 and chunk_size - 1")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        # TODO: split into sentences, group into chunks
        # raise NotImplementedError("Implement SentenceChunker.chunk")
        if not text:
            return []
        # Split into sentences using lookbehind to keep delimiters at the end of sentences
        sentences = [s.strip() for s in re.split(r'(?<=\. |! |\? |\.\n)', text) if s.strip()]
        
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_sentences = sentences[i : i + self.max_sentences_per_chunk]
            chunk_str = " ".join(chunk_sentences)
            chunks.append(chunk_str)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            # Fallback when no separators left: split by fixed size
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        separator = remaining_separators[0]
        # Split current_text by separator
        if separator == "":
            splits = list(current_text)
        else:
            splits = current_text.split(separator)

        # Recursively split any segment that is too large
        next_separators = remaining_separators[1:]
        final_splits = []
        for s in splits:
            if len(s) <= self.chunk_size:
                final_splits.append(s)
            else:
                final_splits.extend(self._split(s, next_separators))

        # Now merge the final splits back together if they fit in chunk_size
        merged_chunks = []
        current_chunk = []
        current_len = 0

        for s in final_splits:
            s_len = len(s)
            sep_len = len(separator) if separator != "" else 0
            addition = sep_len if current_chunk else 0

            if current_len + addition + s_len <= self.chunk_size:
                current_chunk.append(s)
                current_len += addition + s_len
            else:
                if current_chunk:
                    merged_chunks.append(separator.join(current_chunk))
                current_chunk = [s]
                current_len = s_len

        if current_chunk:
            merged_chunks.append(separator.join(current_chunk))

        return merged_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(x * x for x in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_size_chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=chunk_size // 10)
        by_sentences_chunker = SentenceChunker(max_sentences_per_chunk=max(1, chunk_size // 80))
        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)

        strategies = {
            'fixed_size': fixed_size_chunker,
            'by_sentences': by_sentences_chunker,
            'recursive': recursive_chunker
        }

        comparison = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            comparison[name] = {
                'count': count,
                'avg_length': avg_length,
                'chunks': chunks
            }
        return comparison
