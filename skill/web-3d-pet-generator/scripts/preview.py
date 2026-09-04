#!/usr/bin/env python3
import argparse
import functools
import http.server
import webbrowser
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Serve the bundled desktop-pet preview on localhost.")
    parser.add_argument("--port", type=int, default=5193)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=SKILL_ROOT)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    url = f"http://127.0.0.1:{args.port}/assets/preview/"
    print(f"PREVIEW_URL={url}", flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
