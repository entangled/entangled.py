import logging
from rich.console import Console

from rich.logging import RichHandler
from rich.highlighter import RegexHighlighter

from .version import __version__

LOGGING_SETUP = False


class BackTickHighlighter(RegexHighlighter):
    highlights = [r"`(?P<bold>[^`]*)`"]

# Snippet from https://github.com/Textualize/rich/issues/2647#issuecomment-1324286428
class WhitespaceStrippingConsole(Console):
    def _render_buffer(self, *args, **kwargs):
        rendered = super()._render_buffer(*args, **kwargs)
        newline_char = "\n" if rendered[-1] == "\n" else ""
        return "\n".join(line.rstrip() for line in rendered.splitlines()) + newline_char

# Global rich console object
console: Console = WhitespaceStrippingConsole()

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
        handlers=[RichHandler(show_path=debug, highlighter=BackTickHighlighter(), console=console)],
    )
    log = logging.getLogger("entangled")
    # log.setLevel(level)
    # log.addHandler(RichHandler(show_path=debug, highlighter=BackTickHighlighter()))
    # log.propagate = False
    log.debug(f"Entangled {__version__} (https://entangled.github.io/)")

    LOGGING_SETUP = True
