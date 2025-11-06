from pathlib import PurePath
from textwrap import indent
from entangled.model.code_block import CodeBlock
from entangled.text_location import TextLocation

from os import linesep as eol


expected_2 = """
+```
+hello
+
+goodbye
+```
""".lstrip()


expected_3 = """  ```
  hello

  goodbye
  ```
"""


def test_code_block():
    cb = CodeBlock(
        properties=[],
        open_line=f"```{eol}",
        close_line=f"```{eol}",
        source=f"hello{eol}",
        indent="> ",
        origin=TextLocation(PurePath("-"), 1)
    )

    expected = """```\nhello\n```\n"""
    assert cb.text == expected
    assert cb.indented_text == indent(expected.rstrip(), "> ") + "\n"

    cb = CodeBlock(
        properties=[],
        open_line=f"```{eol}",
        close_line=f"```{eol}",
        source=f"hello{eol}{eol}goodbye{eol}",
        indent="+",
        origin=TextLocation(PurePath("-"), 1)
    )
    assert cb.indented_text == expected_2

    cb.indent = "  "
    assert cb.indented_text == expected_3


