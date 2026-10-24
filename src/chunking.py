"""Split markdown documents into chunks that keep their section heading."""
import re
from dataclasses import dataclass

from config import CHUNK_MAX_CHARS, CHUNK_OVERLAP_CHARS


@dataclass
class Chunk:
    doc_name: str
    section: str
    chunk_index: int
    content: str


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Return (heading, body) pairs. Text before the first '## ' heading uses the '# ' title."""
    title_match = re.search(r"^# (.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Introduction"
    parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
    sections = []
    intro = re.sub(r"^# .+$", "", parts[0], flags=re.MULTILINE).strip()
    if intro:
        sections.append((title, intro))
    for i in range(1, len(parts), 2):
        heading, body = parts[i].strip(), parts[i + 1].strip()
        if body:
            sections.append((f"{title} > {heading}", body))
    return sections


def _window(body: str) -> list[str]:
    """Cap long sections: split on paragraph boundaries, with a small overlap between pieces."""
    if len(body) <= CHUNK_MAX_CHARS:
        return [body]
    pieces, current = [], ""
    for para in body.split("\n\n"):
        if current and len(current) + len(para) + 2 > CHUNK_MAX_CHARS:
            pieces.append(current.strip())
            current = current[-CHUNK_OVERLAP_CHARS:] + "\n\n"
        current += para + "\n\n"
    if current.strip():
        pieces.append(current.strip())
    return pieces


def chunk_markdown(doc_name: str, text: str) -> list[Chunk]:
    chunks = []
    for section, body in _split_sections(text):
        for piece in _window(body):
            chunks.append(Chunk(doc_name, section, len(chunks), piece))
    return chunks
