import os
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional

from ..backends.factory import get_backend
from ..utils.epub_utils import write_minimal_epub


@dataclass
class TextbookSpec:
    grade: int
    language: str
    topic: str


def build_textbook(spec: TextbookSpec, out_path: str, *, mode: str = "sample", max_tokens: Optional[int] = None) -> str:
    """Build a minimal EPUB from LLM output.

    Parameters
    - spec: grade/language/topic spec for the book
    - out_path: destination .epub path
    - mode: "sample" (fast, minimal tokens) or "full" (longer, multi-chapter)
    - max_tokens: optional cap for generation; if None, uses a sensible default per mode

    Notes
    - sample mode is optimized to complete in minimal tokens while still yielding a valid EPUB.
    - full mode requests more structure and content and may take longer.
    """
    backend = get_backend()

    if mode not in {"sample", "full"}:
        mode = "sample"

    if max_tokens is None:
        max_tokens = 450 if mode == "sample" else 1800

    if mode == "sample":
        prompt = (
            "You are a textbook author.\n"
            "Create 3 concise sections teaching the topic for the specified grade and language.\n"
            "Each section should be 2-4 short paragraphs. No lists, no code. Keep total under ~450 words.\n\n"
            f"Grade: {spec.grade}\nLanguage: {spec.language}\nTopic: {spec.topic}\n"
            "Output plain text with section headings: Introduction, Practice, Summary."
        )
    else:  # full
        prompt = (
            "You are a textbook author.\n"
            "Write a short textbook with 6 chapters for the specified grade and language.\n"
            "Chapters: 1) Introduction, 2) Concepts, 3) Examples, 4) Practice, 5) Review, 6) Summary.\n"
            "Each chapter should be 3-5 short paragraphs. Plain text only; avoid lists or code.\n\n"
            f"Grade: {spec.grade}\nLanguage: {spec.language}\nTopic: {spec.topic}\n"
            "Output with clear chapter headings like: 'Chapter 1: Introduction', ... 'Chapter 6: Summary'."
        )

    raw = backend.generate(prompt, max_tokens=max_tokens)

    # Split into rough sections; fallback to a single chapter if needed
    sections: List[Tuple[str, str]] = []
    lower = raw.lower()
    parts: List[Tuple[str, int]] = []

    # Heuristics for headings by mode
    if mode == "sample":
        for key in ["introduction", "practice", "summary"]:
            idx = lower.find(key)
            if idx != -1:
                parts.append((key, idx))
    else:
        # Prefer explicit Chapter N headings
        for m in re.finditer(r"\bchapter\s+(\d+)\b", lower):
            num = m.group(1)
            parts.append((f"chapter_{num}", m.start()))
        # Fallback to named chapters if Chapter markers not found
        if not parts:
            for key in ["introduction", "concepts", "examples", "practice", "review", "summary"]:
                idx = lower.find(key)
                if idx != -1:
                    parts.append((key, idx))

    parts.sort(key=lambda x: x[1])

    if parts:
        for i, (name, idx) in enumerate(parts):
            end = parts[i + 1][1] if i + 1 < len(parts) else len(raw)
            # Drop the heading line if present
            segment = raw[idx:end]
            if "\n" in segment:
                body = segment.split("\n", 1)[-1].strip()
            else:
                body = segment.strip()
            if body:
                sections.append((name, body))

    if not sections:
        sections.append((spec.topic, raw.strip()))

    tag = "Sample" if mode == "sample" else "Full"
    safe_title = f"{spec.topic.title()} (Grade {spec.grade}, {spec.language}) — {tag}"
    chapters = [(slug.replace(" ", "_"), body) for slug, body in sections]
    write_minimal_epub(out_path, title=safe_title, author="PlainText.ink", language=spec.language, chapters=chapters)
    return out_path

