import argh  # type: ignore
import logging
import sys

from rich.logging import RichHandler
from rich.highlighter import RegexHighlighter

from .commands import tangle, stitch, sync, watch, status, loom
from .errors.internal import bug_contact
from .errors.user import UserError
from .version import __version__


class BackTickHighlighter(RegexHighlighter):
    highlights = [r"`(?P<bold>[^`]*)`"]


def configure(debug=False):
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
    logging.info(f"Entangled {__version__} (https://entangled.github.io/)")


def cli():
    import argparse

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-d", "--debug", action="store_true", help="enable debug messages"
        )
        parser.add_argument(
            "-v", "--version", action="store_true", help="show version number"
        )
        argh.add_commands(parser, [tangle, stitch, sync, watch, status, loom])
        args = parser.parse_args()

        if args.version:
            print(f"Entangled {__version__}")
            sys.exit(0)

        configure(args.debug)
        argh.dispatch(parser)
    except KeyboardInterrupt:
        logging.info("Goodbye")
        sys.exit(0)
    except UserError as e:
        logging.info(str(e))
        sys.exit(0)
    except Exception as e:
        logging.error(str(e))
        bug_contact(e)
        sys.exit(1)


if __name__ == "__main__":
    cli()
