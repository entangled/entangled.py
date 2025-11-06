from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, fields
import json
from pathlib import Path
from typing import final, override, cast

from ..config import AnnotationMethod
from ..io import Transaction

from ..model import CodeBlock, ReferenceId, ReferenceMap
from ..model.properties import Class, Property, get_attribute, get_attribute_string, get_classes
from ..model.tangle import tangle_ref
from .base import HookBase
from ..logging import logger

log = logger()


def ensure_list(strs: str | list[str] | object) -> list[str]:
    """Some options may be given either as a list or as a single string,
    where the string is supposed to have a whitespace separated list.
    This function converts from either to a list of strings.
    """
    if isinstance(strs, str):
        return strs.split()
    elif isinstance(strs, list):
        assert all(isinstance(s, str) for s in strs)  # pyright: ignore[reportUnknownVariableType]
        return cast(list[str], strs)
    else:
        raise ValueError(f"Expected string or list, got: {strs}")


@final
class Hook(HookBase):
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

            record: dict[str, object] = {
                f.name: get_attribute(cb.properties, f.name)
                for f in fields(Hook.Recipe)
            }

            record["runner"] = record["runner"] or runner
            record["creates"] = ensure_list(record["creates"]) if record["creates"] else None
            record["requires"] = ensure_list(record["requires"]) if record["requires"] else None
            record["ref"] = ref

            log.debug(f"task: {record}")
            recipe = Hook.Recipe(**record)
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
