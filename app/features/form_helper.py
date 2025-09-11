import os
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

import yaml

from ..backends.factory import get_backend
from ..utils.pdf_utils import write_filled_pdf


@dataclass
class Field:
    name: str
    label: str
    type: str = "string"
    required: bool = False


def load_schema(path: str) -> List[Field]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    fields = []
    for item in data.get("fields", []):
        fields.append(
            Field(
                name=item.get("name"),
                label=item.get("label", item.get("name")),
                type=item.get("type", "string"),
                required=bool(item.get("required", False)),
            )
        )
    return fields


def autofill_answers(fields: List[Field]) -> Dict[str, Any]:
    backend = get_backend()
    schema_text = "\n".join(
        f"- {f.label} ({f.type}{', required' if f.required else ''})" for f in fields
    )
    prompt = (
        "You are a helpful form-filling assistant.\n"
        "Given the fields, produce plausible example values as JSON object with keys by field name.\n"
        "Only output JSON.\n\nFields:\n" + schema_text
    )
    raw = backend.generate(prompt, max_tokens=400)
    # Very defensive parse: find first '{' and last '}'
    start = raw.find("{")
    end = raw.rfind("}")
    out: Dict[str, Any] = {}
    if start != -1 and end != -1 and end > start:
        try:
            import json

            out = json.loads(raw[start : end + 1])
        except Exception:
            pass
    # Fill any missing with placeholders
    for f in fields:
        out.setdefault(f.name, f"<{f.label}>")
    return out


def interactive_answers(fields: List[Field]) -> Dict[str, Any]:
    answers: Dict[str, Any] = {}
    for f in fields:
        while True:
            val = input(f"{f.label}{' *' if f.required else ''}: ").strip()
            if val or not f.required:
                answers[f.name] = val
                break
    return answers


def fill_form_to_pdf(schema_path: str, out_pdf: str, interactive: bool = False) -> Tuple[str, Dict[str, Any]]:
    fields = load_schema(schema_path)
    if not fields:
        raise ValueError("Schema contains no fields")
    answers = interactive_answers(fields) if interactive else autofill_answers(fields)
    title = f"Filled Form - {os.path.splitext(os.path.basename(schema_path))[0]}"
    pairs: Tuple[Tuple[str, str], ...] = tuple((f.label, str(answers.get(f.name, ""))) for f in fields)
    write_filled_pdf(out_pdf, title=title, fields=pairs)
    return out_pdf, answers

