import http.server
import socketserver
import os
import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path so 'app' is importable even if CWD differs
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backends.factory import get_backend
from app.features.letter_explainer import explain_letter
from app.features.form_helper import fill_form_to_pdf
from app.features.textbook_builder import TextbookSpec, build_textbook


class Handler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def do_POST(self):  # noqa: N802
        if self.path == "/api/generate":
            try:
                length = int(self.headers.get('Content-Length', '0'))
                data = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(data.decode("utf-8")) if data else {}
                prompt = str(payload.get("prompt", "")).strip()
                max_tokens = int(payload.get("max_tokens", 512))
                if not prompt:
                    self._send_json({"ok": False, "error": "Missing 'prompt'"}, status=400)
                    return
                be = get_backend()  # respects PLAIN_BACKEND; defaults to ollama
                out = be.generate(prompt, max_tokens=max_tokens)
                meta = {"backend": type(be).__name__}
                # expose model if present (e.g., OllamaBackend)
                model = getattr(be, "model", None)
                if model:
                    meta["model"] = model
                if not (isinstance(out, str) and out.strip()):
                    self._send_json({"ok": False, "error": "Empty response from backend", **meta}, status=500)
                    return
                self._send_json({
                    "ok": True,
                    "output": out,
                    **meta,
                })
            except Exception as e:  # pragma: no cover - dev server
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return
        elif self.path == "/api/generate_stream":
            # Stream tokens via SSE when available (Ollama), otherwise send one final event
            try:
                length = int(self.headers.get('Content-Length', '0'))
                data = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(data.decode("utf-8")) if data else {}
                prompt = str(payload.get("prompt", "")).strip()
                max_tokens = int(payload.get("max_tokens", 512))
                if not prompt:
                    self._send_json({"ok": False, "error": "Missing 'prompt'"}, status=400)
                    return
                be = get_backend()
                # Prepare SSE headers
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()

                def sse(ev: str, obj: dict | str):
                    if isinstance(obj, dict):
                        body = json.dumps(obj)
                    else:
                        body = str(obj)
                    msg = f"event: {ev}\ndata: {body}\n\n".encode("utf-8")
                    self.wfile.write(msg)
                    try:
                        self.wfile.flush()
                    except Exception:
                        pass

                # Send meta
                meta = {"backend": type(be).__name__}
                model = getattr(be, "model", None)
                if model:
                    meta["model"] = model
                sse("meta", meta)

                # Try streaming with Ollama client if present
                client = getattr(be, "client", None)
                try:
                    if client is not None:
                        stream = client.generate(
                            model=getattr(be, "model", None) or "",
                            prompt=prompt,
                            options={
                                "num_predict": max_tokens,
                                "temperature": 0.2,
                                "top_p": 0.9,
                            },
                            stream=True,
                        )
                        for chunk in stream:
                            piece = chunk.get("response", "")
                            if piece:
                                sse("delta", {"text": piece})
                        sse("done", {"ok": True})
                        return
                except Exception as e:
                    # Fall back below
                    sse("info", {"note": f"stream fallback: {e}"})

                # Fallback: non-streaming
                out = be.generate(prompt, max_tokens=max_tokens)
                if not out.strip():
                    sse("done", {"ok": False, "error": "Empty response"})
                else:
                    sse("delta", {"text": out})
                    sse("done", {"ok": True})
            except Exception as e:
                # In SSE mode, we can only write plain data lines
                try:
                    self.wfile.write(f"event: done\ndata: {{\"ok\": false, \"error\": \"{str(e)}\"}}\n\n".encode("utf-8"))
                except Exception:
                    pass
            return
        elif self.path == "/api/explain_letter":
            try:
                length = int(self.headers.get('Content-Length', '0'))
                data = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(data.decode("utf-8")) if data else {}
                input_path = str(payload.get("input_path") or "content/letters/sample_medi_cal.pdf")
                res = explain_letter(input_path)
                self._send_json({
                    "ok": True,
                    "summary": res.summary,
                    "checklist": res.checklist,
                })
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return
        elif self.path == "/api/build_textbook":
            try:
                length = int(self.headers.get('Content-Length', '0'))
                data = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(data.decode("utf-8")) if data else {}
                grade = int(payload.get("grade", 5))
                lang = str(payload.get("lang", "en"))
                topic = str(payload.get("topic", "fractions"))
                mode = str(payload.get("mode", "sample"))
                out = payload.get("out") or os.path.join("out", f"textbook_g{grade}_{lang}_{topic.replace(' ', '_')}.epub")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                spec = TextbookSpec(grade=grade, language=lang, topic=topic)
                path = build_textbook(spec, out, mode=mode)
                rel = "/" + os.path.relpath(path, start=os.getcwd())
                self._send_json({"ok": True, "epub": rel, "mode": mode})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return
        elif self.path == "/api/form_fill":
            try:
                length = int(self.headers.get('Content-Length', '0'))
                data = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(data.decode("utf-8")) if data else {}
                schema = str(payload.get("schema") or "content/forms/snap.yaml")
                out = str(payload.get("out") or "out/filled.pdf")
                interactive = bool(payload.get("interactive", False))
                if interactive:
                    # Interactive mode cannot be supported via HTTP
                    self._send_json({"ok": False, "error": "interactive mode not supported via HTTP"}, status=400)
                    return
                os.makedirs(os.path.dirname(out), exist_ok=True)
                out_pdf, answers = fill_form_to_pdf(schema, out, interactive=False)
                rel = "/" + os.path.relpath(out_pdf, start=os.getcwd())
                self._send_json({"ok": True, "pdf": rel, "answers": answers})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
            return
        return super().do_POST()

    def _send_json(self, obj, status: int = 200):  # helper
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main(port: int = 8000):
    # Serve from project root so relative paths like ../content/... work from layout/page.html
    root = ROOT
    os.chdir(root)
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), Handler) as httpd:
        print(f"Serving BookDook at http://127.0.0.1:{port}/layout/page.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()


if __name__ == "__main__":
    # PORT can be provided via env or first CLI arg
    port = int(os.getenv("PORT", "0") or 0)
    if not port and len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except Exception:
            port = 8000
    if not port:
        port = 8000
    main(port)
