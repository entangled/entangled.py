from ..logging import configure, logger
from ..version import __version__

import sys
import rich_click as click


@click.group(
    invoke_without_command=True,
    epilog="See https://entangled.github.io/ for more help and tutorials."
)
@click.rich_config({"commands_before_options": True, "theme": "nord-modern"})
@click.option("-v", "--version", is_flag=True, help="Show version.")
@click.option("-d", "--debug", is_flag=True, help="Enable debugging.")
def main(version: bool = False, debug: bool = False):
    """Your literate programming toolkit.
    """
    if version:
        print(f"Entangled {__version__}")
        sys.exit(0)

    configure(debug)
    logger().debug(f"Welcome to Entangled v{__version__}!")

