from typing import Optional
from pathlib import Path
from itertools import chain
from threading import Event
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .sync import sync
from ..config import config
from ..status import find_watch_dirs


class EventHandler(FileSystemEventHandler):
    def __init__(self):
        self.update_watched()

    def update_watched(self):
        self.watched = find_watch_dirs()

    def on_any_event(self, event: FileSystemEvent):
        if event.event_type == "opened":
            return
        config.read()
        path = Path(event.src_path)
        if path.absolute().is_relative_to(Path("./.entangled").absolute()):
            return
        if any(path.absolute().is_relative_to(p.absolute()) for p in self.watched):
            sync()
            # os.sync()
        self.update_watched()


def _watch(_stop_event: Optional[Event] = None, _start_event: Optional[Event] = None):
    """Keep a loop running, watching for changes. This interface is separated
    from the CLI one, so that it can be tested using threading instead of
    subprocess."""

    def stop() -> bool:
        return _stop_event is not None and _stop_event.is_set()

    sync()

    event_handler = EventHandler()
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()

    if _start_event:
        _start_event.set()

    try:
        while observer.is_alive() and not stop():
            observer.join(0.1)
    finally:
        observer.stop()
        observer.join()


def watch():
    """Keep a loop running, watching for changes."""
    config.read()
    _watch()
