from __future__ import annotations

import re

from .chunking import RecursiveChunker


class SonCustomChunker:
    """Custom policy chunker used by the vnbson branch benchmark."""

    HEADING_RE = re.compile(r"^(#{1,4})\s+(.+)", re.MULTILINE)
    CLAUSE_RE = re.compile(r"^(Điều\s+\d+|Mục\s+\d+|Chương\s+\d+)[.:\s]", re.MULTILINE)
    NUMBERED_RE = re.compile(r"^(\d+(?:\.\d+)*)[.)]\s+", re.MULTILINE)
    FAQ_RE = re.compile(
        r"^(Q\s*\d*|A\s*\d*|Hỏi\s*\d*|Đáp\s*\d*|Câu\s*hỏi\s*\d+|Trả\s*lời\s*\d*)\s*[.:]\s*",
        re.MULTILINE | re.IGNORECASE,
    )

    def __init__(self, max_chunk_size: int = 1000, min_chunk_size: int = 50) -> None:
        if max_chunk_size <= 0:
            raise ValueError("max_chunk_size must be greater than 0")
        if min_chunk_size < 0:
            raise ValueError("min_chunk_size must be greater than or equal to 0")
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self._fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        text = text.strip()
        sections = self._split_by_matches(text, list(self.HEADING_RE.finditer(text)))
        if sections is None:
            clause_matches = list(self.CLAUSE_RE.finditer(text))
            if len(clause_matches) < 2:
                clause_matches = list(self.NUMBERED_RE.finditer(text))
            sections = self._split_by_matches(text, clause_matches)
        if sections is None:
            sections = self._split_faq(text)
        if sections is None:
            return self._fallback.chunk(text)

        chunks: list[str] = []
        for heading, body in sections:
            section = f"{heading}\n{body}".strip() if heading else body.strip()
            if not section:
                continue
            if len(section) <= self.max_chunk_size:
                chunks.append(section)
                continue
            for sub_chunk in self._fallback.chunk(body.strip()):
                chunks.append(f"{heading}\n{sub_chunk}".strip() if heading else sub_chunk)
        return self._merge_small(chunks)

    @staticmethod
    def _split_by_matches(text: str, matches: list[re.Match]) -> list[tuple[str, str]] | None:
        if len(matches) < 2:
            return None
        sections: list[tuple[str, str]] = []
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("", preamble))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections.append((match.group(0).strip(), text[match.end() : end].strip()))
        return sections

    def _split_faq(self, text: str) -> list[tuple[str, str]] | None:
        matches = list(self.FAQ_RE.finditer(text))
        if len(matches) < 2:
            return None
        sections: list[tuple[str, str]] = []
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("", preamble))
        index = 0
        while index < len(matches):
            start = matches[index].start()
            if index + 1 < len(matches):
                current = matches[index].group(1).strip().lower()
                following = matches[index + 1].group(1).strip().lower()
                is_question = any(current.startswith(prefix) for prefix in ("q", "hỏi", "câu"))
                is_answer = any(following.startswith(prefix) for prefix in ("a", "đáp", "trả"))
                if is_question and is_answer:
                    end = matches[index + 2].start() if index + 2 < len(matches) else len(text)
                    sections.append(("", text[start:end].strip()))
                    index += 2
                    continue
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections.append(("", text[start:end].strip()))
            index += 1
        return sections if len(sections) >= 2 else None

    def _merge_small(self, chunks: list[str]) -> list[str]:
        if not chunks:
            return []
        merged = [chunks[0]]
        for chunk in chunks[1:]:
            if len(chunk) < self.min_chunk_size:
                merged[-1] = f"{merged[-1]}\n\n{chunk}"
            else:
                merged.append(chunk)
        return merged


# Backward-compatible name used by the first version of the demo API.
StructuredPolicyChunker = SonCustomChunker
