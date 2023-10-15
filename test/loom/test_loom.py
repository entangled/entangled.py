from dataclasses import dataclass
from typing import Optional
import pytest
from contextlib import asynccontextmanager, chdir
from pathlib import Path
import time
from entangled.loom.task import TaskDB
from entangled.loom.rule import LoomTask, Target, Phony
from entangled.filedb import stat


@dataclass
class Elapsed:
    time: Optional[float] = None


@asynccontextmanager
async def timer():
    e = Elapsed()
    t = time.perf_counter()
    yield e
    e.time = time.perf_counter() - t


class FileTaskDB(TaskDB[Target, None]):
    pass


@pytest.mark.asyncio
async def test_hello(tmp_path: Path):
    with chdir(tmp_path):
        db = FileTaskDB()
        tgt = Path("hello.txt")
        db.add(LoomTask(
            [tgt], [], "Python", script=\
            f"with open('{tgt}', 'w') as f:\n" \
            f"   print(\"Hello, World!\", file=f)\n"))
        db.add(LoomTask([Phony("all")], [tgt]))

        await db.run(Phony("all"))
        time.sleep(0.1)
        assert tgt.exists()
        assert tgt.read_text() == "Hello, World!\n"


@pytest.mark.asyncio
async def test_hello_stdout(tmp_path: Path):
    with chdir(tmp_path):
        db = FileTaskDB()
        tgt = Path("hello.txt")
        db.add(LoomTask([tgt], [], "Python", stdout=tgt, script=\
            "print(\"Hello, World!\")\n"))
        db.add(LoomTask([Phony("all")], [tgt]))

        await db.run(Phony("all"))
        time.sleep(0.1)
        assert tgt.exists()
        assert tgt.read_text() == "Hello, World!\n"


@pytest.mark.asyncio
async def test_runtime(tmp_path: Path):
    with chdir(tmp_path):
        db = FileTaskDB()
        for a in range(4):
            db.add(LoomTask(
                [Phony(f"sleep{a}")], [], "Bash",
                script=f"sleep 0.2\n"))
        db.add(LoomTask([Phony("all")], [Phony(f"sleep{a}") for a in range(4)]))
        async with timer() as t:
            await db.run(Phony("all"))

        assert t.time is not None
        assert t.time > 0.1 and t.time < 0.4

