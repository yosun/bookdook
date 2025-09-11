import os
from dataclasses import dataclass
from typing import List, Tuple

from ..backends.factory import get_backend
from ..utils.epub_utils import write_minimal_epub


@dataclass
class TextbookSpec:
    grade: int
    language: str
    topic: str


def build_textbook(spec: TextbookSpec, out_path: str) -> str:
    backend = get_backend()
    prompt = (
        "You are a textbook author.\n"
        "Create 3 concise sections teaching the topic for the specified grade and language.\n"
        "Each section should be 2-4 short paragraphs without lists or code.\n\n"
        f"Grade: {spec.grade}\nLanguage: {spec.language}\nTopic: {spec.topic}\n"
        "Output sections labeled Introduction, Practice, Summary with plain text."
    )
    raw = backend.generate(prompt, max_tokens=800)

    # Split into rough sections; fallback to a single chapter if needed
    sections: List[Tuple[str, str]] = []
    lower = raw.lower()
    parts = []
    for key in ["introduction", "practice", "summary"]:
        idx = lower.find(key)
        if idx != -1:
            parts.append((key, idx))
    parts.sort(key=lambda x: x[1])
    if parts:
        for i, (name, idx) in enumerate(parts):
            end = parts[i + 1][1] if i + 1 < len(parts) else len(raw)
            body = raw[idx:end].split("\n", 1)[-1].strip()
            sections.append((name, body))
    else:
        sections.append((spec.topic, raw))

    safe_title = f"{spec.topic.title()} (Grade {spec.grade}, {spec.language})"
    chapters = [(slug.replace(" ", "_"), body) for slug, body in sections]
    write_minimal_epub(out_path, title=safe_title, author="PlainText.ink", language=spec.language, chapters=chapters)
    return out_path

