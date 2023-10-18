from typing import Optional
import argh  # type: ignore
import asyncio

from ..config import config
from ..loom import resolve_tasks, Target


async def main(target_strs: list[str], force_run: bool, throttle: Optional[int]):
    db = await resolve_tasks(config.loom)
    if throttle:
        db.throttle = asyncio.Semaphore(throttle)
    db.force_run = force_run
    jobs = [db.run(Target.from_str(t)) for t in target_strs]
    await asyncio.gather(*jobs)


@argh.arg(
    "targets", nargs="*", default=["phony(all)"],
    help="name of target to run"
)
@argh.arg(
    "-B", "--force-run", help="rebuild all dependencies"
)
@argh.arg(
    "-j", "--throttle", help="limit number of concurrent jobs"
)
def loom(targets: list[str], force_run: bool = False, throttle: Optional[int] = None):
    """Build one of the configured targets."""
    asyncio.run(main(targets, force_run, throttle))

