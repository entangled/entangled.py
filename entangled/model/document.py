from dataclasses import dataclass, field
from pathlib import PurePath

from ..config.config_data import Config
from .reference_id import ReferenceId
from .reference_map import ReferenceMap
from .code_block import CodeBlock
from .tangle import tangle_ref


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


@dataclass
class Document:
    config: Config = Config()
    reference_map: ReferenceMap = field(default_factory=ReferenceMap)
    content: dict[PurePath, list[Content]] = field(default_factory=dict)

    def source_text(self, path: PurePath) -> str:
        return "".join(content_to_text(self.reference_map, c) for c in self.content[path])

    def target_text(self, path: PurePath) -> tuple[str, set[PurePath]]:
        ref_name = self.reference_map.select_by_target(path)
        return tangle_ref(self.reference_map, ref_name, self.config.annotation)
