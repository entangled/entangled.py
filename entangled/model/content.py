from dataclasses import dataclass
from .code_block import CodeBlock
from .reference_id import ReferenceId


@dataclass
class PlainText:
    content: str


type RawContent = PlainText | CodeBlock
type Content = PlainText | ReferenceId


