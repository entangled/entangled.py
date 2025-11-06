from pathlib import PurePath
from textwrap import indent
from entangled.model.code_block import CodeBlock
from entangled.text_location import TextLocation


def test_code_block():
    cb = CodeBlock(
        properties=[],
        open_line="```\n",
        close_line="```\n",
        source="hello\n",
        indent="> ",
        origin=TextLocation(PurePath("-"), 1)
    )

    expected = """```\nhello\n```\n"""
    assert cb.text == expected
    assert cb.indented_text == indent(expected.rstrip(), "> ") + "\n"
