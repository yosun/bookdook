import os
from dataclasses import dataclass
from typing import Tuple

from ..backends.factory import get_backend
from ..utils.pdf_utils import extract_text_from_pdf, ensure_sample_pdf


LETTER_PROMPT = (
    "You are a helpful assistant that explains official letters in plain language.\n"
    "Summarize the letter in simple terms and provide a checklist of next steps.\n"
    "Output format:\nSummary:\n- <2-4 bullet points>\nChecklist:\n- <3-6 action items>\n\n"
    "Letter:\n{letter_text}"
)


@dataclass
class LetterExplanation:
    summary: str
    checklist: str


def _parse_response(text: str) -> LetterExplanation:
    # Very lightweight parsing into sections
    lower = text.lower()
    s_idx = lower.find("summary")
    c_idx = lower.find("checklist")
    if s_idx != -1 and c_idx != -1:
        summary = text[s_idx:text.find("\n", s_idx) + 1] + text[s_idx + 7 : c_idx]
        checklist = text[c_idx:]
        return LetterExplanation(summary=summary.strip(), checklist=checklist.strip())
    return LetterExplanation(summary=text.strip(), checklist="- Verify details\n- Take action")


def load_letter_text(path: str) -> str:
    if not os.path.exists(path):
        # If they referenced sample_medi_cal.pdf and it's missing, generate a minimal one
        if path.endswith(".pdf"):
            ensure_sample_pdf(path, title="Sample Medi-Cal Letter", body=(
                "Dear Member,\n\nThis is a sample benefits notice used for demos.\n"
                "It explains eligibility and steps to confirm information.\n"
                "Please review and respond by the listed date.\n\nSincerely,\nAgency"
            ))
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write("This is a sample letter in plain text for the demo.")

    if path.lower().endswith(".pdf"):
        return extract_text_from_pdf(path)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


def explain_letter(path: str) -> LetterExplanation:
    text = load_letter_text(path)
    prompt = LETTER_PROMPT.format(letter_text=text[:8000])  # guard against huge PDFs
    backend = get_backend()
    response = backend.generate(prompt)
    return _parse_response(response)

