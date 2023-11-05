from __future__ import annotations
from dataclasses import dataclass, fields
import json
from pathlib import Path
from typing import Any

from ..document import CodeBlock, ReferenceId, ReferenceMap
from ..properties import Class, Property, get_attribute, get_classes
from .base import HookBase


class Hook(HookBase):
    class Config(HookBase.Config):
        pass

    @dataclass()
    class Recipe:
        description: str | None
        target: str
        requires: list[str] | None
        runner: str | None
        stdout: str | None
        stdin: str | None
        script: str

        def to_brei_task(self):
            return {
                "description": self.description,
                "creates": [self.target],
                "requires": self.requires or [],
                "runner": self.runner,
                "stdout": self.stdout,
                "stdin": self.stdin,
                "script": self.script
            }

    def __init__(self, config: Hook.Config):
        self.recipes: list[Hook.Recipe] = []
        self.config = config

    def condition(self, props: list[Property]):
        return (
            "task" in get_classes(props) and
            get_attribute(props, "target") is not None
        )

    def on_read(self, refs: ReferenceMap, ref: ReferenceId, cb: CodeBlock):
        target = get_attribute(cb.properties, "target")
        if target is None:
            return

        match cb.properties[0]:
            case Class("task"):
                runner = None
            case Class(lang_id):
                runner = lang_id
            case _:
                return

        record: dict[str, Any] = {
            f.name: get_attribute(cb.properties, f.name)
            for f in fields(Hook.Recipe)
        }
        record["runner"] = record["runner"] or runner
        record["requires"] = record["requires"].split() if record["requires"] else None
        self.recipes.append(Hook.Recipe(**record))
    
    def post_tangle(self, _: ReferenceMap):
        targets = [r.target for r in self.recipes]
        collect = {
            "name": "weave-tasks",
            "requires": targets
        }
        with open(Path(".entangled/weave.json"), "w") as f_out:
            json.dump({
                "task": [r.to_brei_task() for r in self.recipes] + [collect]
            }, f_out)

