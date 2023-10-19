from .logging import configure, logger

configure(debug=False)

import argh  # type: ignore
import sys
import traceback
import logging

from .commands import new, status, stitch, sync, tangle, watch, loom
from .errors.internal import bug_contact
from .errors.user import HelpfulUserError, UserError
from .version import __version__

def cli():
    import argparse

    log = logger()

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-d", "--debug", action="store_true", help="enable debug messages"
        )
        parser.add_argument(
            "-v", "--version", action="store_true", help="show version number"
        )
        argh.add_commands(parser, [new, loom, status, stitch, sync, tangle, watch])
        args = parser.parse_args()

        if args.version:
            print(f"Entangled {__version__}")
            sys.exit(0)

        if args.debug:
            log.level = logging.DEBUG
        else:
            log.level = logging.INFO

        argh.dispatch(parser)
    except KeyboardInterrupt:
        log.info("Goodbye")
        sys.exit(0)
    except HelpfulUserError as e:
        log.error(e, exc_info=False)
        e.func()
        sys.exit(0)
    except UserError as e:
        log.error(e, exc_info=False)
        sys.exit(0)
    except Exception as e:
        log.error(str(e))
        bug_contact(e)
        traceback.print_exc()
        raise e


if __name__ == "__main__":
    cli()
