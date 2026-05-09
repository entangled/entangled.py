from threading import Event
from pathlib import Path

from ..status import find_watch_dirs
from ..logging import logger

from .sync import run_sync
from .main import main
from ..errors.user import UserError

import watchfiles


log = logger()


def watch_filter(change: watchfiles.Change, path: str) -> bool:
    if Path(path).relative_to(Path.cwd()).as_posix().startswith(".entangled"):
        return False
    return True


def _watch(_stop_event: Event | None = None, _start_event: Event | None = None):
    """Keep a loop running, watching for changes. This interface is separated
    from the CLI one, so that it can be tested using threading instead of
    subprocess."""

    def stop() -> bool:
        return _stop_event is not None and _stop_event.is_set()

    log.debug("Running daemon")
    run_sync()

    if _start_event is not None:
        log.debug("Setting start event")
        _start_event.set()

    dirs = "."  # find_watch_dirs()

    for changes in watchfiles.watch(dirs, stop_event=_stop_event, watch_filter=watch_filter):
        log.debug(changes)
        try:
            run_sync()
        except UserError as e:
            logger().error(e, exc_info=False)


@main.command()
def watch():
    """Keep a loop running, watching for changes."""
    _watch()
