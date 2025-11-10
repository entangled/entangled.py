from dataclasses import dataclass
from .code_block import CodeBlock
from .reference_id import ReferenceId
from .reference_map import ReferenceMap


@dataclass
class PlainText:
    content: str


type RawContent = PlainText | CodeBlock
type Content = PlainText | ReferenceId


def content_to_text(r: ReferenceMap, c: Content) -> str:
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
            return s
        case ReferenceId():
            return r[c].indented_text

