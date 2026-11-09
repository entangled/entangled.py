"""
Filters for `entangled weave`. Each filter is registered by name in `filters`;
the first line of its docstring serves as description for `--list-filters`.
"""

from html import escape
import re

from ..model import CodeBlock, Content, PlainText, ReferenceId, ReferenceMap
from ..model.properties import Attribute, Class, Id
from .base import ContentFilter, codeblock_filter


def block_title(code_block: CodeBlock) -> str | None:
    """Compute a human readable title for a code block from its id and `file`
    attribute. Returns `None` for anonymous code blocks."""
    ids = [p.value for p in code_block.properties if isinstance(p, Id)]
    filenames = [p.value for p in code_block.properties  # pyright: ignore[reportAny]
                 if isinstance(p, Attribute) and p.key == "file"]

    if len(ids) > 1 or len(filenames) > 1:
        return "error: ambiguous code block title"
    if ids and filenames:
        return f"#{ids[0]} / file: {filenames[0]}"
    if ids:
        return f"#{ids[0]}"
    if filenames:
        return f"file: {filenames[0]}"
    return None


def first_line(text: str) -> tuple[str, str]:
    head, nl, rest = text.partition("\n")
    return head, nl + rest


@codeblock_filter
def title(reference_map: ReferenceMap, r: ReferenceId) -> list[Content]:
    """Add a `title` attribute to the code block header (MkDocs/pymdownx style)."""
    code_block = reference_map[r]
    text = block_title(code_block)
    ids = [p.value for p in code_block.properties if isinstance(p, Id)]
    classes = [p.value for p in code_block.properties if isinstance(p, Class)]

    head, rest = first_line(code_block.open_line)
    fence_match = re.match(r"\s*(`{3,}|~{3,})", head)
    fence = fence_match.group(1) if fence_match else "```"

    attrs: list[str] = []
    if ids:
        attrs.append(str(Id(ids[0])))
    attrs.extend(str(Class(c)) for c in classes[1:])
    if text:
        attrs.append(str(Attribute("title", text)))

    head = fence + (classes[0] if classes else "")
    if attrs:
        head += " {" + " ".join(attrs) + "}"

    code_block.open_line = head + (rest or "\n")
    return [r]


@codeblock_filter
def label(reference_map: ReferenceMap, r: ReferenceId) -> list[Content]:
    """Wrap code blocks in a `<div>` with a label; renders in most Markdown previews."""
    code_block = reference_map[r]
    text = block_title(code_block)
    if text is None:
        return [r]

    ind = code_block.indent
    header = (f"{ind}<div class=\"entangled-code-block\" markdown=\"1\">\n"
              f"{ind}<div class=\"entangled-code-title\"><code>{escape(text)}</code></div>\n\n")
    # The closing fence may lack a newline at the end of a file. The blank
    # lines around `</div>` end the HTML block in CommonMark.
    eol = "" if code_block.close_line.endswith("\n") else "\n"
    footer = f"{eol}\n{ind}</div>\n\n"
    return [PlainText(header), r, PlainText(footer)]


filters: dict[str, ContentFilter] = {
    "label": label,
    "title": title,
}


def filter_description(f: ContentFilter) -> str:
    return (f.__doc__ or "").strip().partition("\n")[0]
