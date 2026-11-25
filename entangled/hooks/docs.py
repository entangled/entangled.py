"""
The `docs` hook collects user documentation that is spread over several
chapters into one generated Markdown file. A snippet is marked with the `docs`
class and a `file` attribute, either as a Pandoc fenced div:

    ::: {.docs file=docs/reference.md section="The mel language" order=10}
    `mel("...")` reads a melody from text.

    ```python
    mel("g4:q bb4 d5")
    ```
    :::

or as a Markdown code block:

    ``` {.markdown .docs file=docs/reference.md section="Patches"}
    ...
    ```

Fenced code inside a `docs` div is copied verbatim and not tangled as code of
the chapter. Fenced divs are only recognized when this hook is enabled.

All snippets with the same `file` are written to that file. Snippets without a
`section` come first; then come the sections, each under a heading. Snippets are
sorted by their `order` attribute (default 0), and then in the order they were
read. A section is placed by the lowest `order` among its snippets.

The generated file is an ordinary tangle target in Markdown, so it carries the
usual annotations (`<!-- ~/~ begin <<...>>[0] -->`) and edits can be stitched
back into the chapters.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import PurePath
from typing import final, override

from ..config.language import Comment, Language
from ..model import CodeBlock, ReferenceId, ReferenceMap, ReferenceName
from ..model.properties import Attribute, Property, get_attribute, get_attribute_string, get_classes
from ..logging import logger

from .base import HookBase


log = logger()

DOCS_CLASS = "docs"
TARGET_ATTRIBUTE = "docs-file"
NAMESPACE = ("entangled-docs",)
MARKDOWN = Language("Markdown", ["markdown", "md"], Comment("<!--", "-->"))


def _move_file_attribute(props: list[Property]) -> list[Property]:
    """Rename the `file` attribute, so that the snippet is not a target of
    its own."""
    return [Attribute(TARGET_ATTRIBUTE, p.value)
            if isinstance(p, Attribute) and p.key == "file" else p
            for p in props]


@dataclass
class Snippet:
    ref: ReferenceId
    section: str | None
    order: float
    index: int

    @property
    def key(self) -> tuple[float, int]:
        return (self.order, self.index)


def _order(code: CodeBlock) -> float:
    value = get_attribute(code.properties, "order")
    if value is None:
        return 0
    try:
        return float(value)  # pyright: ignore[reportAny]
    except (TypeError, ValueError):
        log.warning(f"{code.origin}: `order` attribute should be a number, got `{value}`")
        return 0


@final
class Hook(HookBase):
    class Config(HookBase.Config):
        section_level: int = 2

    def __init__(self, config: Hook.Config, state: HookBase.State):
        super().__init__(config, state)
        self.config = config

    @override
    @staticmethod
    def priority() -> int:
        # Run after `quarto_attributes`, which may add the `file` attribute.
        return 20

    @override
    def on_read(self, code: CodeBlock):
        if DOCS_CLASS not in get_classes(code.properties):
            return
        code.properties = _move_file_attribute(code.properties)
        if code.language is None:
            code.language = MARKDOWN

    def section_text(self, section: str | None, snippets: list[Snippet]) -> str:
        lines: list[str] = []
        if section is not None:
            lines.append(f"{'#' * self.config.section_level} {section}\n")

        seen: set[ReferenceName] = set()
        for s in sorted(snippets, key=lambda s: s.key):
            if s.ref.name in seen:
                continue
            seen.add(s.ref.name)
            lines.append(f"<<{s.ref.name}>>\n")

        return "\n".join(lines)

    def document_text(self, snippets: list[Snippet]) -> str:
        sections: defaultdict[str | None, list[Snippet]] = defaultdict(list)
        for s in snippets:
            sections[s.section].append(s)

        def section_key(item: tuple[str | None, list[Snippet]]):
            name, members = item
            return (name is not None, min(s.key for s in members))

        return "\n".join(self.section_text(name, members)
                         for name, members in sorted(sections.items(), key=section_key))

    @override
    def post_read(self, refs: ReferenceMap):
        """Register a generated code block for each documentation target."""
        targets: defaultdict[PurePath, list[Snippet]] = defaultdict(list)
        for index, (ref, code) in enumerate(refs.items()):
            if ref.name.namespace == NAMESPACE:
                continue
            if DOCS_CLASS not in get_classes(code.properties):
                continue
            target = get_attribute_string(code.properties, TARGET_ATTRIBUTE)
            if target is None:
                log.warning(f"{code.origin}: `docs` block without `file` attribute")
                continue
            section = get_attribute(code.properties, "section")
            targets[PurePath(target)].append(Snippet(
                ref, None if section is None else str(section), _order(code), index))  # pyright: ignore[reportAny]

        for target_path, snippets in targets.items():
            name = ReferenceName(NAMESPACE, target_path.as_posix())
            for old in list(refs.select_by_name(name)):
                del refs[old]

            first = refs[min(snippets, key=lambda s: s.index).ref]
            refs[refs.new_id(target_path, name)] = CodeBlock(
                properties=[Attribute("file", target_path.as_posix())],
                indent="",
                open_line="",
                close_line="",
                source=self.document_text(snippets),
                origin=first.origin,
                language=MARKDOWN,
            )
