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
        if not text or not text.strip():
            return []

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:[ \t]+|\n+)", text.strip())
            if sentence.strip()
        ]
        return [
            " ".join(sentences[start : start + self.max_sentences_per_chunk])
            for start in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


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
        if not text or not text.strip():
            return []
        return self._split(text.strip(), self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        if separator == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]
        if separator not in current_text:
            return self._split(current_text, remaining_separators[1:])

        parts = current_text.split(separator)
        chunks: list[str] = []
        pending = ""
        for part in parts:
            part = part.strip()
            if not part:
                continue
            candidate = f"{pending}{separator}{part}" if pending else part
            if len(candidate) <= self.chunk_size:
                pending = candidate
                continue
            if pending:
                chunks.append(pending)
            if len(part) <= self.chunk_size:
                pending = part
            else:
                chunks.extend(self._split(part, remaining_separators[1:]))
                pending = ""
        if pending:
            chunks.append(pending)
        return chunks


class CustomChunker:
    """Chiến lược chia nhỏ tùy chỉnh cho tài liệu chính sách TMĐT / hỗ trợ khách hàng.

    Lý do thiết kế:
        Tài liệu chính sách thường có cấu trúc rõ ràng theo heading (# / ## / ###),
        điều khoản (Điều X, Mục X, 1., 1.1) hoặc dạng FAQ (Hỏi/Đáp, Q/A).
        Việc chia theo ranh giới ngữ nghĩa này giữ nguyên ngữ cảnh mỗi chunk,
        giúp retrieval chính xác hơn so với chia cố định theo ký tự.

    Chiến lược phát hiện (theo thứ tự ưu tiên):
        1. Heading Markdown: dòng bắt đầu bằng # / ## / ###
        2. Điều khoản pháp lý: "Điều X", "Mục X", "Chương X"
        3. Mục đánh số: "1.", "1.1", "1.1.1" ở đầu dòng
        4. FAQ: "Q:", "A:", "Hỏi:", "Đáp:", "Câu hỏi X"

    Nếu không tìm thấy pattern nào, fallback về RecursiveChunker.
    Chunk quá dài sẽ được chia nhỏ tiếp bằng RecursiveChunker.
    """

    # Regex patterns cho từng loại ranh giới
    _HEADING_RE = re.compile(r"^(#{1,4})\s+(.+)", re.MULTILINE)
    _CLAUSE_RE = re.compile(
        r"^(Điều\s+\d+|Mục\s+\d+|Chương\s+\d+)[.:\s]",
        re.MULTILINE,
    )
    _NUMBERED_RE = re.compile(r"^(\d+(?:\.\d+)*)[.)]\s+", re.MULTILINE)
    _FAQ_RE = re.compile(
        r"^(Q\s*\d*|A\s*\d*|Hỏi\s*\d*|Đáp\s*\d*|Câu\s*hỏi\s*\d+|Trả\s*lời\s*\d*)\s*[.:]\s*",
        re.MULTILINE | re.IGNORECASE,
    )

    def __init__(self, max_chunk_size: int = 1000, min_chunk_size: int = 50) -> None:
        if max_chunk_size <= 0:
            raise ValueError("max_chunk_size must be greater than 0")
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self._fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        text = text.strip()

        # Thử phát hiện cấu trúc theo thứ tự ưu tiên
        sections = self._split_by_headings(text)
        if not sections:
            sections = self._split_by_clauses(text)
        if not sections:
            sections = self._split_by_faq(text)
        if not sections:
            # Fallback: dùng RecursiveChunker
            return self._fallback.chunk(text)

        # Xử lý từng section: giữ heading, chia nhỏ nếu quá dài
        chunks: list[str] = []
        for heading, body in sections:
            section_text = f"{heading}\n{body}".strip() if heading else body.strip()
            if not section_text:
                continue

            if len(section_text) <= self.max_chunk_size:
                chunks.append(section_text)
            else:
                # Chia nhỏ body, prefix heading vào mỗi sub-chunk
                sub_chunks = self._fallback.chunk(body.strip())
                for sub in sub_chunks:
                    if heading:
                        prefixed = f"{heading}\n{sub}"
                    else:
                        prefixed = sub
                    chunks.append(prefixed.strip())

        # Gộp chunk quá nhỏ vào chunk trước đó
        return self._merge_small_chunks(chunks)

    def _split_by_headings(self, text: str) -> list[tuple[str, str]] | None:
        """Chia theo heading Markdown (# / ## / ###)."""
        matches = list(self._HEADING_RE.finditer(text))
        if len(matches) < 2:
            return None
        return self._extract_sections(text, matches)

    def _split_by_clauses(self, text: str) -> list[tuple[str, str]] | None:
        """Chia theo điều khoản (Điều X, Mục X, Chương X) hoặc mục đánh số."""
        matches = list(self._CLAUSE_RE.finditer(text))
        if len(matches) < 2:
            # Thử mục đánh số
            matches = list(self._NUMBERED_RE.finditer(text))
        if len(matches) < 2:
            return None
        return self._extract_sections(text, matches)

    def _split_by_faq(self, text: str) -> list[tuple[str, str]] | None:
        """Chia theo dạng FAQ (Q/A, Hỏi/Đáp)."""
        matches = list(self._FAQ_RE.finditer(text))
        if len(matches) < 2:
            return None

        # Gộp cặp Q-A thành 1 chunk
        sections: list[tuple[str, str]] = []

        # Nội dung trước FAQ đầu tiên
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("", preamble))

        i = 0
        while i < len(matches):
            start = matches[i].start()
            # Tìm cặp Q-A: nếu match hiện tại là Q/Hỏi, gộp với A/Đáp tiếp theo
            if i + 1 < len(matches):
                end = matches[i + 2].start() if i + 2 < len(matches) else len(text)
                current_label = matches[i].group(1).strip().lower()
                next_label = matches[i + 1].group(1).strip().lower()

                # Nếu là cặp hỏi-đáp, gộp lại
                is_question = any(
                    current_label.startswith(q) for q in ("q", "hỏi", "câu")
                )
                is_answer = any(
                    next_label.startswith(a) for a in ("a", "đáp", "trả")
                )
                if is_question and is_answer:
                    chunk_text = text[start:end].strip()
                    sections.append(("", chunk_text))
                    i += 2
                    continue

            # Không phải cặp, lấy từng match
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            chunk_text = text[start:end].strip()
            sections.append(("", chunk_text))
            i += 1

        return sections if len(sections) >= 2 else None

    def _extract_sections(
        self, text: str, matches: list[re.Match]
    ) -> list[tuple[str, str]]:
        """Trích xuất sections từ danh sách regex matches."""
        sections: list[tuple[str, str]] = []

        # Nội dung trước section đầu tiên
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("", preamble))

        for i, match in enumerate(matches):
            heading = match.group(0).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            sections.append((heading, body))

        return sections

    def _merge_small_chunks(self, chunks: list[str]) -> list[str]:
        """Gộp chunk quá nhỏ vào chunk liền trước."""
        if not chunks:
            return []
        merged: list[str] = [chunks[0]]
        for chunk in chunks[1:]:
            if len(chunk) < self.min_chunk_size and merged:
                merged[-1] = f"{merged[-1]}\n\n{chunk}"
            else:
                merged.append(chunk)
        return merged


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if len(vec_a) != len(vec_b):
        raise ValueError("vectors must have the same dimensions")
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": sum(map(len, chunks)) / len(chunks) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
