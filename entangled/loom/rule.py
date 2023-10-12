"""
A minimal build system.
"""

from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Optional, Union, Callable
from asyncio import create_subprocess_exec


PROGRAMS: dict[str, tuple[str, list[str]]] = {
    "Python": ("python", []),
    "Bash": ("bash", []),
}


@dataclass
class Rule:
    targets: list[Path]
    dependencies: list[Path]
    language: str
    path: Optional[Path] = None
    script: Optional[str] = None
    stdin: Optional[Path] = None
    stdout: Optional[Path] = None

    def validate(self):
        assert (self.path is None) or (self.script is None)

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

    def call(self, args: Any) -> Rule:
        targets = [Path(t.format(**args)) for t in self.targets]
        deps = [Path(d.format(**args)) for d in self.dependencies]
        lang = self.language
        if self.path is not None:
            script = self.path.read_text().format(**args)
        elif self.script is not None:
            script = self.script.format(**args)
        else:
            raise ValueError("A `Pattern` needs to have either a `path` or `script` defined.")

        return Rule(targets, deps, lang, script=script)


@dataclass
class Config:
    rules: list[Rule] = field(default_factory=list)
    patterns: dict[str, Pattern] = field(default_factory=dict)
    calls: dict[str, Any] = field(default_factory=dict)
    includes: list[Path] = field(default_factory=list)



