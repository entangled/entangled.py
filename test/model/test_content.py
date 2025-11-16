from entangled.text_location import TextLocation
from entangled.model import ReferenceMap, ReferenceId, ReferenceName, CodeBlock
from entangled.model.content import PlainText, content_to_text

from pathlib import PurePath

def test_content_to_text():
    refs = ReferenceMap()
    ref = ReferenceId(ReferenceName((), "a"), PurePath("a.md"), 0)
    code_block = CodeBlock(properties=[], indent="", open_line="", source="x", close_line="", origin=TextLocation(PurePath(""), 0))
    refs[ref] = code_block

    assert content_to_text(refs, ref)[0] == "x"
    assert content_to_text(refs, PlainText("y"))[0] == "y"

