from typing import Awaitable, Optional
import argh  # type: ignore
import asyncio

from ..config import config
from brei import resolve_tasks, Phony
from ..logging import logger

log = logger()


async def main(target_strs: list[str], force_run: bool, throttle: Optional[int]):
    db = await resolve_tasks(config.brei)
    if throttle:
        db.throttle = asyncio.Semaphore(throttle)
    db.force_run = force_run
    jobs: list[Awaitable] = [db.run(Phony(t), db=db) for t in target_strs]
    await asyncio.gather(*jobs)


@argh.arg("targets", nargs="+", help="name of target to run")
@argh.arg("-B", "--force-run", help="rebuild all dependencies")
@argh.arg("-j", "--throttle", help="limit number of concurrent jobs")
def brei(targets: list[str], *, force_run: bool = False, throttle: Optional[int] = None):
    """Build one of the configured targets."""
    config.read()
    asyncio.run(main(targets, force_run, throttle))
