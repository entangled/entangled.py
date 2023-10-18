"""
A minimal build system.
"""

from __future__ import annotations
import asyncio
from contextlib import nullcontext
from copy import copy
from dataclasses import dataclass, field
from pathlib import Path
import logging
from tempfile import NamedTemporaryFile
from typing import Any, ClassVar, Optional, Union
from asyncio import create_subprocess_exec
from typing_extensions import override

from entangled.parsing import (
    Parsable,
    Parser,
    choice,
    fmap,
    fullmatch,
    matching,
    starmap,
)
from .task import MissingDependency, Task, TaskDB
from ..filedb import stat


@dataclass
class Runner:
    command: str
    args: list[str]


DEFAULT_RUNNERS: dict[str, Runner] = {
    "Python": Runner("python", ["{script}"]),
    "Bash": Runner("bash", ["{script}"]),
}


@dataclass
class Phony(Parsable):
    _pattern: ClassVar[Parser] = matching(r"phony\(([^()\s]+)\)")
    name: str

    @staticmethod
    def __parser__() -> Parser[Phony]:
        return Phony._pattern >> starmap(lambda n: Phony(n))

    def __str__(self):
        return f"phony({self.name})"

    def __hash__(self):
        return hash(f"#{self.name}#")


@dataclass
class Target(Parsable):
    phony_or_path: Phony | Path

    @staticmethod
    def __parser__() -> Parser[Target]:
        return choice(Phony, fullmatch(".*") >> fmap(Path)) >> fmap(Target)

    @staticmethod
    def from_str(s: str) -> Target:
        result: Target = Target.__parser__().read(s)[0]
        return result

    def __str__(self):
        return f"Target({self.phony_or_path})"

    def __hash__(self):
        return hash(self.phony_or_path)

    def is_phony(self) -> bool:
        return isinstance(self.phony_or_path, Phony)

    def is_path(self) -> bool:
        return isinstance(self.phony_or_path, Path)

    @property
    def path(self) -> Path:
        if not isinstance(self.phony_or_path, Path):
            raise ValueError("Not a path")
        return self.phony_or_path


@dataclass
class LoomTask(Task[Target, None]):
    language: Optional[str] = None
    path: Optional[Path] = None
    script: Optional[str] = None
    stdin: Optional[Path] = None
    stdout: Optional[Path] = None

    def validate(self):
        assert (self.path is None) or (self.script is None)
        if self.stdin is not None:
            assert Target(self.stdin) in self.dependencies
        if self.stdout is not None:
            assert Target(self.stdout) in self.targets

    def always_run(self) -> bool:
        dep_paths = [p.path for p in self.dependencies if p.is_path()]
        if not dep_paths:
            return True
        return False

    def needs_run(self) -> bool:
        target_paths = [t.path for t in self.targets if t.is_path()]
        dep_paths = [p.path for p in self.dependencies if p.is_path()]
        if any(not path.exists() for path in target_paths):
            return True
        target_stats = [stat(p) for p in target_paths]
        dep_stats = [stat(p) for p in dep_paths]
        if any(t < d for t in target_stats for d in dep_stats):
            return True
        return False

    async def run(self, cfg):
        if not self.always_run() and not self.needs_run() and not cfg.force_run:
            return

        if self.language is None or (self.path is None and self.script is None):
            return

        runner = cfg.runners[self.language]
        if self.path is not None:
            tmpfile = None
            path = self.path
        elif self.script is not None:
            tmpfile = NamedTemporaryFile("w")
            tmpfile.write(self.script)
            tmpfile.flush()
            path = Path(tmpfile.name)
        else:
            raise ValueError("A `Rule` can have either `path` or `script` defined.")

        args = [arg.format(script=path) for arg in runner.args]
        stdin = open(self.stdin, "r") if self.stdin is not None else None
        stdout = open(self.stdout, "w") if self.stdout is not None else None

        tgt_str = "(" + " ".join(str(t) for t in self.targets) + ")"
        logging.info(f"{tgt_str} -> {runner.command} " + " ".join(args))
        async with cfg.throttle or nullcontext():
            proc = await create_subprocess_exec(
                runner.command, *args, stdin=stdin, stdout=stdout
            )
        await proc.communicate()

        if tmpfile is not None:
            tmpfile.close()

        assert not self.needs_run()


@dataclass
class LoomTaskDB(TaskDB[Target, LoomTask]):
    runners: dict[str, Runner] = field(default_factory=lambda: copy(DEFAULT_RUNNERS))
    throttle: Optional[asyncio.Semaphore] = None
    force_run: bool = False

    async def run(self, t: Target, *args):
        return await super().run(t, self, *args)

    def on_missing(self, t: Target):
        if not t.is_path() or not t.path.exists():
            raise MissingDependency()
        return LoomTask([t], [])

    def target(self, target_path: Union[str, Path], deps: list[Target], **kwargs):
        target_path = Path(target_path)
        task = LoomTask([Target(target_path)], deps, **kwargs)
        self.add(task)

    def phony(self, target_name: str, deps: list[Target], **kwargs):
        task = LoomTask([Target(Phony(target_name))], deps, **kwargs)
        self.add(task)


@dataclass
class Pattern:
    """NYI. A `Pattern` can be used to generate `Rule`s from a template.
    This template will be expanded using Jinja."""

    targets: list[str]
    dependencies: list[str] = field(default_factory=list)
    language: Optional[str] = None
    path: Optional[Path] = None
    script: Optional[str] = None
    stdout: Optional[str] = None
    stdin: Optional[str] = None

    def validate(self):
        assert (self.path is None) ^ (self.script is None)

    def call(self, args: dict[str, Any]) -> LoomTask:
        targets: list[Target] = [
            Target.from_str(t.format(**args)) for t in self.targets
        ]
        deps: list[Target] = [
            Target.from_str(d.format(**args)) for d in self.dependencies
        ]
        lang = self.language
        if self.path is not None:
            script = self.path.read_text().format(**args)
        elif self.script is not None:
            script = self.script.format(**args)
        else:
            raise ValueError(
                "A `Pattern` needs to have either a `path` or `script` defined."
            )

        stdout = Path(self.stdout.format(**args)) if self.stdout is not None else None
        stdin = Path(self.stdin.format(**args)) if self.stdin is not None else None
        return LoomTask(targets, deps, lang, script=script, stdout=stdout, stdin=stdin)
