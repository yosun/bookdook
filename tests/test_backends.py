import os

from app.backends.factory import get_backend


def test_dummy_backend_selection():
    os.environ["PLAIN_BACKEND"] = "dummy"
    be = get_backend()
    out = be.generate("Hello")
    assert "DUMMY" in out.upper()

