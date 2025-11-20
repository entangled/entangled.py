from .logging import logger

import sys
import traceback

from .commands import main
from .errors.internal import bug_contact
from .errors.user import HelpfulUserError, UserError
from .version import __version__


def cli():
    try:
        main()
    except KeyboardInterrupt:
        logger().info("Goodbye")
        sys.exit(0)
    except HelpfulUserError as e:
        e.handle()
    except UserError as e:
        logger().error(e, exc_info=False)
        sys.exit(0)
    except Exception as e:
        logger().error(str(e))
        bug_contact(e)
        traceback.print_exc()
        raise e


if __name__ == "__main__":
    cli()
