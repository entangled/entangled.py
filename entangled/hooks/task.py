from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, fields
import json
from pathlib import Path
from typing import Any

from ..config import AnnotationMethod
from ..transaction import Transaction

from ..document import CodeBlock, ReferenceId, ReferenceMap
from ..properties import Class, Property, get_attribute, get_classes
from .base import HookBase
from ..logging import logger
from ..tangle import tangle_ref

log = logger()

class Hook(HookBase):
    @dataclass
    class Config(HookBase.Config):
        pass

    @dataclass
    class Recipe:
        description: str | None
        creates: list[str] | None
        requires: list[str] | None
        runner: str | None
        stdout: str | None
        stdin: str | None
        collect: str | None
        ref: ReferenceId

        def to_brei_task(self, refs: ReferenceMap):
            cb = refs[self.ref]
            if (path := get_attribute(cb.properties, "file")) is None:
                script, _ = tangle_ref(refs, self.ref.name, AnnotationMethod.NAKED)
            else:
                script = None

            return {
                "description": self.description,
                "creates": self.creates or [],
                "requires": self.requires or [],
                "runner": self.runner,
                "stdout": self.stdout,
                "stdin": self.stdin,
                "script": script,
                "path": path
            }

    def __init__(self, config: Hook.Config):
        self.recipes: list[Hook.Recipe] = []
        self.collections: dict[str, list[str]] = defaultdict(list)
        self.config = config
        self.sources: list[Path] = []

    def condition(self, props: list[Property]):
        return (
            "task" in get_classes(props)
        )

    def on_read(self, refs: ReferenceMap, ref: ReferenceId, cb: CodeBlock):
        self.sources.append(Path(ref.file))

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
        record["creates"] = record["creates"].split() if record["creates"] else None
        record["requires"] = record["requires"].split() if record["requires"] else None
        record["ref"] = ref

        log.debug(f"task: {record}")
        recipe = Hook.Recipe(**record)
        self.recipes.append(recipe)
        if recipe.collect:
            targets = recipe.creates or []
            if recipe.stdout:
                targets.append(recipe.stdout)
            self.collections[recipe.collect].extend(targets)
    
    def on_tangle(self, t: Transaction, refs: ReferenceMap):
        collect = [{
            "name": k,
            "requires": tgts
        } for k, tgts in self.collections.items()]
        content = json.dumps({
                "task": [r.to_brei_task(refs) for r in self.recipes] + collect
            }, indent=2)
        t.write(Path(".entangled/tasks.json"), content, self.sources, mode=0o444)

