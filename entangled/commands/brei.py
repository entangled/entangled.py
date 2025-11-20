from pathlib import Path
from collections.abc import Awaitable
from typing import Any
import asyncio
import textwrap

from ..config import Config, read_config
from brei import resolve_tasks, Phony
from ..logging import logger
from .main import main

import click

log = logger()


async def brei_main(target_strs: list[str], force_run: bool, throttle: int | None):
    if not Path(".entangled").exists():
        Path(".entangled").mkdir()

    cfg = Config() | read_config()
    db = await resolve_tasks(cfg.brei, Path(".entangled/brei_history"))
    if throttle:
        db.throttle = asyncio.Semaphore(throttle)
    db.force_run = force_run
    jobs: list[Awaitable[Any]] = [db.run(Phony(t), db=db) for t in target_strs]
    with db.persistent_history():
        results = await asyncio.gather(*jobs)

    log.debug(f"{results}")
    if not all(results):
        log.error("Some jobs have failed:")
        for r in results:
            if not r:
                msg = textwrap.indent(str(r), "| ")
                log.error(msg)


@main.command()
@click.argument("targets", nargs=-1)
@click.option("-B", "--force-run", is_flag=True, help="rebuild all dependencies")
@click.option("-j", "--throttle", is_flag=True, help="limit number of concurrent jobs")
def brei(targets: list[str], *, force_run: bool = False, throttle: int | None = None):
    """Build one of the configured targets.

    TARGETS     Names of the targets to run.
    """
    asyncio.run(brei_main(targets, force_run, throttle))
