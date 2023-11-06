import logging
from rich.logging import RichHandler
from rich.highlighter import RegexHighlighter

from .version import __version__

LOGGING_SETUP = False


class BackTickHighlighter(RegexHighlighter):
    highlights = [r"`(?P<bold>[^`]*)`"]


def logger():
    return logging.getLogger("entangled")


def configure(debug=False):
    global LOGGING_SETUP
    if LOGGING_SETUP:
        return

    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    FORMAT = "%(message)s"
    logging.basicConfig(
        level=level,
        format=FORMAT,
        datefmt="[%X]",
        handlers=[RichHandler(show_path=debug, highlighter=BackTickHighlighter())],
    )
    log = logging.getLogger("entangled")
    # log.setLevel(level)
    # log.addHandler(RichHandler(show_path=debug, highlighter=BackTickHighlighter()))
    # log.propagate = False
    log.debug(f"Entangled {__version__} (https://entangled.github.io/)")

    LOGGING_SETUP = True
