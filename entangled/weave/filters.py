"""
Filters for `entangled weave`. Each filter is registered by name in `filters`;
the first line of its docstring serves as description for `--list-filters`.
"""

from base64 import b64encode
from functools import lru_cache
from html import escape
from io import StringIO
from pathlib import Path
from textwrap import indent
import re

import msgspec

from repl_session import ReplCommand, ReplOutput, ReplSession, read_session

from ..hooks.repl import strip_comments
from ..logging import logger
from ..model import CodeBlock, Content, PlainText, ReferenceId, ReferenceMap
from ..model.properties import Attribute, Class, Id, get_attribute_string
from .base import ContentFilter, codeblock_filter


log = logger()


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


# Representations to pick from a MIME bundle, most preferred first.
MIME_PRIORITY = [
    "text/markdown", "text/html", "image/svg+xml", "image/png", "image/jpeg", "image/gif",
    "text/plain",
]


def fenced(text: str, classes: list[str]) -> str:
    """Put text in a fenced code block, with a fence longer than any backtick
    run inside the text."""
    longest = max((len(m) for m in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    attrs = " ".join(str(Class(c)) for c in classes)
    return f"{fence} {{{attrs}}}\n{text}\n{fence}"


def render_mime(mime: str, data: str, kind: str) -> str | None:
    """Render a single representation as Markdown, or `None` if there is
    nothing to show."""
    match mime:
        case "text/plain":
            text = data.strip("\n")
            if not text.strip():
                return None
            return fenced(text, ["text", "output"] + ([] if kind == "result" else [kind]))
        case "text/markdown" | "text/html":
            return data.strip("\n") or None
        case "image/svg+xml":
            return f"![](data:{mime};base64,{b64encode(data.encode()).decode()})"
        case _ if mime.startswith("image/"):
            return f"![](data:{mime};base64,{"".join(data.split())})"
        case _:
            return None


def render_output(output: ReplOutput, output_type: str) -> str | None:
    """Render the most preferred representation in an output's MIME bundle.
    A `mime-type` set on the code block, other than the default `text/plain`,
    takes precedence."""
    preferred = [] if output_type == "text/plain" else [output_type]
    for mime in [*preferred, *MIME_PRIORITY]:
        if mime in output.data:
            return render_mime(mime, output.data[mime], output.kind)
    return None


def command_outputs(command: ReplCommand) -> list[ReplOutput]:
    """Outputs of a command; sessions from older versions of `repl-session`
    only have the `output` field."""
    if command.outputs is not None:
        return command.outputs
    if command.output is None:
        return []
    return [ReplOutput("result", {command.output_type: command.output})]


@lru_cache(maxsize=16)
def decode_session(text: str) -> ReplSession:
    """Decode the output of a REPL session. Every code block in the session
    needs it, so we cache on the contents of the file; modification times
    are too coarse to tell when a file was rewritten."""
    return read_session(StringIO(text))


def session_output(path: Path) -> ReplSession | None:
    try:
        return decode_session(path.read_text())
    except FileNotFoundError:
        log.warning("REPL session output `%s` not found; run `repl-session` first.", path)
    except msgspec.MsgspecError as e:
        log.warning("REPL session output `%s` could not be read: %s", path, e)
    return None


def find_command(reference_map: ReferenceMap, r: ReferenceId) -> ReplCommand | None:
    """Find the command for a code block in the output of its REPL session.
    The session is opened by the first code block of the same name that has
    the `repl` class and a `session` attribute; every code block of that name
    from there on is a command in the session."""
    refs = reference_map.select_by_name(r.name)
    try:
        start = next(i for i, ref in enumerate(refs)
                     if Class("repl") in reference_map[ref].properties
                     and get_attribute_string(reference_map[ref].properties, "session"))
    except StopIteration:
        return None

    session_file = get_attribute_string(reference_map[refs[start]].properties, "session")
    assert session_file is not None
    session = session_output(Path(session_file).with_suffix(".out.json"))
    if session is None:
        return None

    index = refs.index(r) - start
    code_block = reference_map[r]
    if not 0 <= index < len(session.commands):
        log.warning("%s: no output for this code block in REPL session `%s`.",
                    code_block.origin, session_file)
        return None

    command = session.commands[index]
    if code_block.language is not None \
            and command.command.strip() != strip_comments(code_block.source, code_block.language).strip():
        log.warning("%s: REPL session `%s` is out of date; tangle and run `repl-session` again.",
                    code_block.origin, session_file)
        return None
    return command


@codeblock_filter
def repl(reference_map: ReferenceMap, r: ReferenceId) -> list[Content]:
    """Insert the output of REPL sessions (from the `repl` hook) after code blocks with the `repl` class."""
    code_block = reference_map[r]
    if Class("repl") not in code_block.properties:
        return [r]

    command = find_command(reference_map, r)
    if command is None:
        return [r]

    rendered = [text for out in command_outputs(command)
                if (text := render_output(out, command.output_type)) is not None]
    if not rendered:
        return [r]

    # The closing fence may lack a newline at the end of a file.
    eol = "" if code_block.close_line.endswith("\n") else "\n"
    body = "".join(indent(f"\n{text}\n", code_block.indent) for text in rendered)
    return [r, PlainText(eol + body)]


filters: dict[str, ContentFilter] = {
    "label": label,
    "repl": repl,
    "title": title,
}


def filter_description(f: ContentFilter) -> str:
    return (f.__doc__ or "").strip().partition("\n")[0]
