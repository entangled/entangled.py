from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
from typing import final, override

from ..config import AnnotationMethod
from ..io import Transaction

from ..model import ReferenceId, ReferenceMap
from ..model.properties import Class, get_attribute_string, get_classes, get_typed_attribute
from ..model.tangle import tangle_ref
from .base import HookBase
from ..logging import logger

log = logger()


@final
class Hook(HookBase):
    @dataclass
    class Recipe:
        ref: ReferenceId
        description: str | None = None
        creates: list[str] | None = None
        requires: list[str] | None = None
        runner: str | None = None
        stdout: str | None = None
        stdin: str | None = None
        collect: str | None = None

        def to_brei_task(self, refs: ReferenceMap):
            cb = refs[self.ref]
            if (path := get_attribute_string(cb.properties, "file")) is None:
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
        super().__init__(config)
        self.recipes: list[Hook.Recipe] = []
        self.collections: dict[str, list[str]] = defaultdict(list)
        self.config = config
        self.sources: list[Path] = []

    @override
    def pre_tangle(self, refs: ReferenceMap):
        for ref, cb in refs.items():
            if "task" not in get_classes(cb.properties):
                continue

            self.sources.append(Path(ref.file))

            match cb.properties[0]:
                case Class("task"):
                    runner = None
                case Class(lang_id):
                    runner = lang_id
                case _:
                    continue

            recipe = Hook.Recipe(
                ref=ref,
                description=get_typed_attribute(str, cb.properties, "description"),
                creates=get_typed_attribute(list[str], cb.properties, "creates"),
                requires=get_typed_attribute(list[str], cb.properties, "requires"),
                runner=get_typed_attribute(str, cb.properties, "runner") or runner,
                stdout=get_typed_attribute(str, cb.properties, "stdout"),
                stdin=get_typed_attribute(str, cb.properties, "stdin"),
                collect=get_typed_attribute(str, cb.properties, "collect")
            )
            self.recipes.append(recipe)
            if recipe.collect:
                targets = recipe.creates or []
                if recipe.stdout:
                    targets.append(recipe.stdout)
                self.collections[recipe.collect].extend(targets)

    @override
    def on_tangle(self, t: Transaction, refs: ReferenceMap):
        collect = [{
            "name": k,
            "requires": tgts
        } for k, tgts in self.collections.items()]
        content = json.dumps({
                "task": [r.to_brei_task(refs) for r in self.recipes] + collect
            }, indent=2)
        t.write(Path(".entangled/tasks.json"), content, self.sources, mode=0o444)
