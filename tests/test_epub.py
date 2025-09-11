import os
from app.features.textbook_builder import TextbookSpec, build_textbook


def test_build_epub_tmp(tmp_path):
    os.environ["PLAIN_BACKEND"] = "dummy"
    out = tmp_path / "tb.epub"
    spec = TextbookSpec(grade=5, language="en", topic="fractions")
    path = build_textbook(spec, str(out))
    assert os.path.exists(path)
    assert os.path.getsize(path) > 100

