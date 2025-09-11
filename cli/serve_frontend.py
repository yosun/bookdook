import http.server
import socketserver
import os
from pathlib import Path


def main(port: int = 8000):
    # Serve from project root so relative paths like ../content/... work from layout/page.html
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving BookDook at http://127.0.0.1:{port}/layout/page.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()


if __name__ == "__main__":
    main()
