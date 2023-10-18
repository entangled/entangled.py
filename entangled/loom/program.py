from __future__ import annotations
from copy import copy
import logging
from typing import Any, Generic, Optional
from dataclasses import dataclass, field, asdict, fields
from pathlib import Path

import tomlkit

from entangled.errors.user import UserError

from ..construct import construct
from .file_task import DEFAULT_RUNNERS, LoomTask, LoomTaskDB, Pattern, Runner, Target


@dataclass
class MissingInclude(UserError):
    path: Path

    def __str__(self):
        return f"Include `{self.path}` not found."


@dataclass
class MissingPattern(UserError):
    name: str

    def __str__(self):
        return f"Pattern `{self.name}` not found."


@dataclass
class PatternCall:
    pattern: str
    args: dict[str, Any]


@dataclass
class TaskProxy:
    targets: list[Target]
    dependencies: list[Target] = field(default_factory=list)
    language: Optional[str] = None
    path: Optional[Path] = None
    script: Optional[str] = None
    stdin: Optional[Path] = None
    stdout: Optional[Path] = None


@dataclass
class LoomProgram:
    task: list[TaskProxy] = field(default_factory=list)
    pattern: dict[str, Pattern] = field(default_factory=dict)
    call: list[PatternCall] = field(default_factory=list)
    include: list[Path] = field(default_factory=list)
    runner: dict[str, Runner] = field(default_factory=dict)

    def write(self, path: Path):
        with open(path, "w") as f_out:
            tomlkit.dump(self.__dict__, f_out)

    @staticmethod
    def read(path: Path) -> LoomProgram:
        with open(path, "r") as f_in:
            data = tomlkit.load(f_in)
        return construct(LoomProgram, data)


async def resolve_tasks(program: LoomProgram) -> LoomTaskDB:
    db = LoomTaskDB()
    pattern_index = dict()

    async def go(program: LoomProgram):
        tasks = [LoomTask(**t.__dict__) for t in program.task]
        pattern_index.update(program.pattern)
        delayed_calls: list[PatternCall] = []

        db.runners.update(program.runner)

        for t in tasks:
            db.add(t)

        for c in program.call:
            if c.pattern not in pattern_index:
                logging.debug(
                    "pattern `%s` not available, waiting for includes to resolve",
                    c.pattern,
                )
                delayed_calls.append(c)
                continue
            p = pattern_index[c.pattern]
            task = p.call(c.args)
            db.add(task)

        for inc in program.include:
            if Target(inc) in db.index:
                await db.run(Target(inc))
            if not inc.exists():
                raise MissingInclude(inc)

            prg = LoomProgram.read(inc)
            await go(prg)

        for c in delayed_calls:
            if c.pattern not in pattern_index:
                logging.debug(
                    "pattern `%s` still not available, now this is an error", c.pattern
                )
                raise MissingPattern(c.pattern)
            p = pattern_index[c.pattern]
            db.add(p.call(c.args))

        return db

    return await go(program)
