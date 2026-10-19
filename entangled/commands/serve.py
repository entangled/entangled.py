from ..server.server import Reloader, Handler
from .main import main
from ..logging import logger

from functools import partial
from pathlib import Path
import subprocess
import threading
from http.server import ThreadingHTTPServer

from watchfiles import watch
import click


def watch_site(site: Path, reloader: Reloader):
    for changes in watch(site):
        logger().info(f"[livereload] {len(changes)} change(s) in {site}, reloading")
        reloader.trigger()


def watch_sources(paths: list[Path], site: Path, build: str):
    def is_source(_change, path: str) -> bool:
        return not Path(path).resolve().is_relative_to(site.resolve())

    for _ in watch(*paths, watch_filter=is_source):
        logger().info(f"[livereload] sources changed, running: {build}")
        subprocess.run(build, shell=True, check=False)


@main.command()
@click.argument("directory", type=Path, help="directory to serve")
@click.option("-p", "--port", type=int, default=8000)
@click.option("-b", "--bind", default="127.0.0.1")
@click.option("--build", help="shell command to run when sources change")
@click.option("-w", "--watch", type=Path, multiple=True, help="source paths for --build")
def serve(directory: Path, port: int, bind: str, build: str | None = None, watch: list[Path] | None = None) -> None:
    """Stand-alone webserver with browser auto-reloading."""
    reloader = Reloader()
    threading.Thread(
        target=watch_site, args=(directory, reloader), daemon=True
    ).start()
    if build:
        threading.Thread(
            target=watch_sources,
            args=(watch or [Path(".")], directory, build),
            daemon=True,
        ).start()

    handler = partial(Handler, directory=str(directory))
    Handler.reloader = reloader
    with ThreadingHTTPServer((bind, port), handler) as server:
        server.daemon_threads = True
        logger().info(f"[livereload] serving {directory} at http://{bind}:{port}/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
