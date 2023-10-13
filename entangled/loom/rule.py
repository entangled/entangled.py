"""
A minimal build system.
"""

from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Optional, Union, Callable
from asyncio import create_subprocess_exec
from .task import Task, TaskDB
from ..filedb import stat

PROGRAMS: dict[str, tuple[str, list[str]]] = {
    "Python": ("python", []),
    "Bash": ("bash", [])
}

@dataclass
class Phony:
    name: str

Target = Union[Path, Phony]

@dataclass
class LoomTask(Task[Target, None]):
    language: str
    path: Optional[Path] = None
    script: Optional[str] = None
    stdin: Optional[Path] = None
    stdout: Optional[Path] = None

    def validate(self):
        assert (self.path is None) or (self.script is None)
        if self.stdin is not None:
            assert self.stdin in self.dependencies
        if self.stdout is not None:
            assert self.stdout in self.targets

    def needs_run(self) -> bool:
        target_paths = [t for t in self.targets if isinstance(t, Path)]
        if any(not path.exists() for path in target_paths):
            return True
        target_stats = [stat(p) for p in target_paths]
        dep_stats = [stat(p) for p in self.dependencies if isinstance(p, Path)]
        if any()

    async def run(self):
        program, args = PROGRAMS[self.language]
        if self.path is not None:
            tmpfile = None
            path = self.path
        elif self.script is not None:
            tmpfile = NamedTemporaryFile("w")
            tmpfile.write(self.script)
            path = Path(tmpfile.name)
        else:
            raise ValueError("A `Rule` can have either `path` or `script` defined.")
        
        args = [arg.format(script=path) for arg in args]
        await create_subprocess_exec(program, *args)

        if tmpfile is not None:
            tmpfile.close()


@dataclass
class Pattern:
    """NYI. A `Pattern` can be used to generate `Rule`s from a template.
    This template will be expanded using Jinja."""
    targets: list[str]
    dependencies: list[str]
    language: str
    path: Optional[Path]
    script: Optional[str]

    def validate(self):
        assert (self.path is None) ^ (self.script is None)

    def call(self, args: Any) -> LoomTask:
        targets: list[Target] = [Path(t.format(**args)) for t in self.targets]
        deps: list[Target] = [Path(d.format(**args)) for d in self.dependencies]
        lang = self.language
        if self.path is not None:
            script = self.path.read_text().format(**args)
        elif self.script is not None:
            script = self.script.format(**args)
        else:
            raise ValueError("A `Pattern` needs to have either a `path` or `script` defined.")

        return LoomTask(targets, deps, lang, script=script)


@dataclass
class Config:
    tasks: list[LoomTask] = field(default_factory=list)
    patterns: dict[str, Pattern] = field(default_factory=dict)
    calls: dict[str, Any] = field(default_factory=dict)
    includes: list[Path] = field(default_factory=list)



