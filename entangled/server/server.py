"""Minimal live-reloading static file server.

Serves a directory over HTTP, injects a tiny script into every HTML page,
and tells connected browsers to reload (via Server-Sent Events) whenever
something in the served directory changes. Optionally runs a build command
whenever source files change.

    python serve.py docs/site --build "entangled tangle && brei weave" --watch docs
"""

import argparse
import functools
import subprocess
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from watchfiles import watch

EVENT_PATH = "/__livereload"
SNIPPET = (
    f'<script>new EventSource("{EVENT_PATH}")'
    '.addEventListener("reload", () => location.reload());</script>'
).encode()


class Reloader:
    """Generation counter that SSE handlers block on."""

    def __init__(self):
        self.generation = 0
        self.cond = threading.Condition()

    def trigger(self):
        with self.cond:
            self.generation += 1
            self.cond.notify_all()

    def wait(self, generation: int, timeout: float) -> int:
        with self.cond:
            self.cond.wait_for(lambda: self.generation != generation, timeout)
            return self.generation


class Handler(SimpleHTTPRequestHandler):
    reloader: Reloader

    def do_GET(self):
        if self.path == EVENT_PATH:
            return self.serve_events()
        path = Path(self.translate_path(self.path))
        if path.is_dir():
            path = path / "index.html"
        if path.suffix == ".html" and path.is_file():
            return self.serve_html(path)
        return super().do_GET()

    def serve_html(self, path: Path):
        body = path.read_bytes()
        i = body.rfind(b"</body>")
        body = body[:i] + SNIPPET + body[i:] if i >= 0 else body + SNIPPET
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def serve_events(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        generation = self.reloader.generation
        try:
            while True:
                new = self.reloader.wait(generation, timeout=15)
                if new != generation:
                    generation = new
                    self.wfile.write(b"event: reload\ndata: \n\n")
                else:
                    self.wfile.write(b": keepalive\n\n")  # detects closed tabs
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format, *args):
        if self.path != EVENT_PATH:
            super().log_message(format, *args)


def watch_site(site: Path, reloader: Reloader):
    for changes in watch(site):
        print(f"[livereload] {len(changes)} change(s) in {site}, reloading", flush=True)
        reloader.trigger()


def watch_sources(paths: list[Path], site: Path, build: str):
    def is_source(_change, path: str) -> bool:
        return not Path(path).resolve().is_relative_to(site.resolve())

    for _ in watch(*paths, watch_filter=is_source):
        print(f"[livereload] sources changed, running: {build}", flush=True)
        subprocess.run(build, shell=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path, help="directory to serve")
    parser.add_argument("-p", "--port", type=int, default=8000)
    parser.add_argument("-b", "--bind", default="127.0.0.1")
    parser.add_argument("--build", help="shell command to run when sources change")
    parser.add_argument(
        "--watch", type=Path, nargs="*", default=[], help="source paths for --build"
    )
    args = parser.parse_args()

    reloader = Reloader()
    threading.Thread(
        target=watch_site, args=(args.directory, reloader), daemon=True
    ).start()
    if args.build:
        threading.Thread(
            target=watch_sources,
            args=(args.watch or [Path(".")], args.directory, args.build),
            daemon=True,
        ).start()

    handler = functools.partial(Handler, directory=str(args.directory))
    Handler.reloader = reloader
    with ThreadingHTTPServer((args.bind, args.port), handler) as server:
        server.daemon_threads = True
        print(f"[livereload] serving {args.directory} at http://{args.bind}:{args.port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
