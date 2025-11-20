from dataclasses import dataclass
from pathlib import PurePath
from .code_block import CodeBlock
from .reference_id import ReferenceId
from .reference_map import ReferenceMap


@dataclass
class PlainText:
    content: str


type RawContent = PlainText | CodeBlock
type Content = PlainText | ReferenceId


def content_to_text(r: ReferenceMap, c: Content) -> tuple[str, PurePath | None]:
    """
    Reconstruct original plain text from a piece of content.

    Args:
        r: the reference map.
        c: the content.

    Returns:
        A string, usually not terminated by a newline.
    """
    match c:
        case PlainText(s):
            return s, None
        case ReferenceId():
            code_block = r[c]
            return code_block.indented_text, code_block.origin.filename

