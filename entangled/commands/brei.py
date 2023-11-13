from pathlib import Path
from typing import Awaitable, Optional
import argh  # type: ignore
import asyncio
import textwrap

from ..config import config
from brei import resolve_tasks, Phony
from ..logging import logger

log = logger()


async def main(target_strs: list[str], force_run: bool, throttle: Optional[int]):
    if not Path(".entangled").exists():
        Path(".entangled").mkdir()

    db = await resolve_tasks(config.brei, Path(".entangled/brei_history"))
    if throttle:
        db.throttle = asyncio.Semaphore(throttle)
    db.force_run = force_run
    jobs: list[Awaitable] = [db.run(Phony(t), db=db) for t in target_strs]
    with db.persistent_history():
        results = await asyncio.gather(*jobs)

    log.debug(f"{results}")
    if not all(results):
        log.error("Some jobs have failed:")
        for r in results:
            if not r:
                msg = textwrap.indent(str(r), "| ")
                log.error(msg)


@argh.arg("targets", nargs="+", help="name of target to run")
@argh.arg("-B", "--force-run", help="rebuild all dependencies")
@argh.arg("-j", "--throttle", help="limit number of concurrent jobs")
def brei(targets: list[str], *, force_run: bool = False, throttle: Optional[int] = None):
    """Build one of the configured targets."""
    config.read()
    asyncio.run(main(targets, force_run, throttle))

