from dataclasses import dataclass
import os
from typing import Optional, Union
import pytest
from contextlib import asynccontextmanager, chdir
from pathlib import Path
import time
from entangled.filedb import stat
from entangled.loom.file_task import LoomTaskDB, Phony, Target


@dataclass
class Elapsed:
    time: Optional[float] = None


@asynccontextmanager
async def timer():
    e = Elapsed()
    t = time.perf_counter()
    yield e
    e.time = time.perf_counter() - t


@pytest.mark.asyncio
async def test_hello(tmp_path: Path):
    with chdir(tmp_path):
        db = LoomTaskDB()
        tgt = Path("hello.txt")
        db.target(tgt, [], language="Python", script=\
            f"with open('{tgt}', 'w') as f:\n" \
            f"   print(\"Hello, World!\", file=f)\n")
        db.phony("all", [Target(tgt)])

        await db.run(Target(Phony("all")))
        os.sync()
        assert tgt.exists()
        assert tgt.read_text() == "Hello, World!\n"


@pytest.mark.asyncio
async def test_hello_stdout(tmp_path: Path):
    with chdir(tmp_path):
        db = LoomTaskDB()
        tgt = Path("hello.txt")
        db.target(tgt, [], language="Python", stdout=tgt, script=\
            "print(\"Hello, World!\")\n")
        db.phony("all", [Target(tgt)])

        await db.run(Target(Phony("all")))
        os.sync()
        assert tgt.exists()
        assert tgt.read_text() == "Hello, World!\n"


@pytest.mark.asyncio
async def test_runtime(tmp_path: Path):
    with chdir(tmp_path):
        db = LoomTaskDB()
        for a in range(4):
            db.phony(
                f"sleep{a}", [], language="Bash",
                script=f"sleep 0.2\n")
        db.phony("all", [Target(Phony(f"sleep{a}")) for a in range(4)])
        async with timer() as t:
            await db.run(Target(Phony("all")))

        assert t.time is not None
        assert t.time > 0.1 and t.time < 0.4


@pytest.mark.asyncio
async def test_rebuild(tmp_path: Path):
    with chdir(tmp_path):
        db = LoomTaskDB()

        # Set input
        i1, i2 = (Path(f"i{n}") for n in [1, 2])
        i1.write_text("1\n")
        i2.write_text("3\n")

        # Make tasks
        a, b, c = (Path(x) for x in "abc")
        # a = i1 + 1
        db.target(a, [Target(i1)], language="Python", stdout=a,
                  script="print(int(open('i1','r').read()) + 1)")
        # b = a * i2
        db.target(b, [Target(a), Target(i2)], language="Python", stdout=b,
                  script="print(int(open('a','r').read()) * int(open('i2','r').read()))")
        # c = a + b
        db.target(c, [Target(a), Target(b)], language="Python", stdout=c,
                  script="print(int(open('b','r').read()) * int(open('a','r').read()))")
        await db.run(Target(c))
        assert all(x.exists() for x in (a, b, c))
        assert c.read_text() == "12\n"

        i2.write_text("4\n")
        os.sync()

        assert not db.index[Target(a)].needs_run()
        assert db.index[Target(b)].needs_run()

        db.reset()
        await db.run(Target(c))
        os.sync()

        assert stat(a) < stat(i2)
        assert a.read_text() == "2\n"
        assert b.read_text() == "8\n"
        assert c.read_text() == "16\n"

