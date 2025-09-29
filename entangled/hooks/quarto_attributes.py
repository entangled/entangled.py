from __future__ import annotations
from typing import Any, final, override
import yaml

from entangled.config.language import Language

from ..properties import Attribute, Class, Id, Property
from ..document import CodeBlock
from .base import HookBase
from ..logging import logger


log = logger()


def get_code_properties(source: str, language: Language) -> list[Property]:
    props: list[Property] = []

    trigger = f"{language.comment.open}|"
    header = "\n".join(
        line[len(trigger):] for line in source.splitlines()
        if line.startswith(trigger))

    attrs = yaml.safe_load(header)
    if attrs is None:
        return props
    if not isinstance(attrs, dict):
        log.warning("quarto attributes do not evaluate to dictionary; skipping")
        log.warning(f"tried to parse: {header}")
        return props

    if "id" in attrs.keys():
        assert isinstance(attrs["id"], str)
        props.append(Id(attrs["id"]))

    if "classes" in attrs.keys():
        props.extend(Class(c) for c in attrs["classes"])

    props.extend(Attribute(k, v) for k, v in attrs.items()
                 if k not in ("id", "classes"))

    return props


@final
class Hook(HookBase):
    def __init__(self, config: Hook.Config):
        super().__init__(config)
        self.config = config

    @override
    def on_read(self, code: CodeBlock):
        log.debug("quarto filter: %s", code)

        if code.language is None:
            return

        extra_props = get_code_properties(code.source, code.language)
        log.debug("quarto attributes: %s", extra_props)

        code.properties.extend(extra_props)
