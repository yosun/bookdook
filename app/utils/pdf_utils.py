import os
from typing import Tuple

from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(t.strip() for t in texts if t and t.strip())


def ensure_sample_pdf(path: str, title: str = "Sample Letter", body: str = "Hello from PlainText.ink!") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    c.setTitle(title)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, title)
    c.setFont("Helvetica", 11)
    text = c.beginText(72, height - 108)
    for line in body.splitlines():
        text.textLine(line)
    c.drawText(text)
    c.showPage()
    c.save()


def write_filled_pdf(path: str, title: str, fields: Tuple[Tuple[str, str], ...]) -> None:
    """Write a very simple PDF listing field names and values.

    This avoids relying on pre-existing AcroForm templates for the MVP.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    c.setTitle(title)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, height - 72, title)
    c.setFont("Helvetica", 11)
    y = height - 108
    for name, value in fields:
        if y < 100:
            c.showPage()
            y = height - 72
            c.setFont("Helvetica", 11)
        c.drawString(72, y, f"{name}: {value}")
        y -= 18
    c.showPage()
    c.save()

