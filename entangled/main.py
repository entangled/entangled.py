import argh  # type: ignore
import logging
import sys


try:
    from rich.logging import RichHandler
    from rich.highlighter import RegexHighlighter

    WITH_RICH = True
except ImportError:
    WITH_RICH = False


from .commands import new, status, stitch, sync, tangle, watch
from .errors.internal import bug_contact
from .errors.user import HelpfulUserError, UserError
from .version import __version__


if WITH_RICH:

    class BackTickHighlighter(RegexHighlighter):
        highlights = [r"`(?P<bold>[^`]*)`"]


def configure(debug=False):
    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    if WITH_RICH:
        FORMAT = "%(message)s"
        logging.basicConfig(
            level=level,
            format=FORMAT,
            datefmt="[%X]",
            handlers=[RichHandler(show_path=debug, highlighter=BackTickHighlighter())],
        )
        logging.debug("Rich logging enabled")
    else:
        logging.basicConfig(level=level)
        logging.debug("Plain logging enabled")

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
        argh.add_commands(parser, [new, status, stitch, sync, tangle, watch])
        args = parser.parse_args()

        if args.version:
            print(f"Entangled {__version__}")
            sys.exit(0)

        configure(args.debug)
        argh.dispatch(parser)
    except KeyboardInterrupt:
        logging.info("Goodbye")
        sys.exit(0)
    except HelpfulUserError as e:
        logging.error(e, exc_info=False)
        e.func()
        sys.exit(0)
    except UserError as e:
        logging.error(e, exc_info=False)
        sys.exit(0)
    except Exception as e:
        logging.error(str(e))
        bug_contact(e)
        sys.exit(1)


if __name__ == "__main__":
    cli()
