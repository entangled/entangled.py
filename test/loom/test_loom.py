from dataclasses import dataclass
import os
from typing import Optional
import pytest
from contextlib import asynccontextmanager, chdir
from pathlib import Path
import time
from entangled.loom.task import TaskDB
from entangled.loom.file_task import LoomTask, Target, Phony


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
    def target(self, target_path: Path, deps: list[Target], **kwargs):
        task = LoomTask([target_path], deps, **kwargs)
        self.add(task)

    def phony(self, target_name: str, deps: list[Target], **kwargs):
        task = LoomTask([Phony(target_name)], deps, **kwargs)
        self.add(task)


@pytest.mark.asyncio
async def test_hello(tmp_path: Path):
    with chdir(tmp_path):
        db = FileTaskDB()
        tgt = Path("hello.txt")
        db.target(tgt, [], language="Python", script=\
            f"with open('{tgt}', 'w') as f:\n" \
            f"   print(\"Hello, World!\", file=f)\n")
        db.phony("all", [tgt])

        await db.run(Phony("all"))
        os.sync()
        assert tgt.exists()
        assert tgt.read_text() == "Hello, World!\n"


@pytest.mark.asyncio
async def test_hello_stdout(tmp_path: Path):
    with chdir(tmp_path):
        db = FileTaskDB()
        tgt = Path("hello.txt")
        db.target(tgt, [], language="Python", stdout=tgt, script=\
            "print(\"Hello, World!\")\n")
        db.phony("all", [tgt])

        await db.run(Phony("all"))
        os.sync()
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


# @pytest.mark.asyncio
# async def test_rebuild(tmp_path: Path):
#     with chdir(tmp_path):
#         db = FileTaskDB()
#         db.
