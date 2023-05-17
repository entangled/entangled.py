from pathlib import Path
from itertools import chain
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .sync import sync
from ..config import config
from ..filedb import file_db


class EventHandler(FileSystemEventHandler):
    def __init__(self):
        input_file_list = chain.from_iterable(map(Path(".").glob, config.watch_list))
        markdown_dirs = set(p.parent for p in input_file_list)
        with file_db(readonly=True) as db:
            code_dirs = set(p.parent for p in db.managed)
        self.watched = code_dirs.union(markdown_dirs)

    def on_any_event(self, event: FileSystemEvent):
        if event.event_type == "opened":
            return
        path = Path(event.src_path)
        if path.is_relative_to(Path("./.entangled")):
            return
        if any(path.is_relative_to(p) for p in self.watched):
            sync()


def watch():
    """Keep a loop running, watching for changes."""
    sync()

    event_handler = EventHandler()
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()

    try:
        while observer.is_alive():
            observer.join(1.0)
    finally:
        observer.stop()
        observer.join()
