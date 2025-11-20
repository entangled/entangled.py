from entangled.interface import Document
from entangled.model import ReferenceId
from entangled.io import VirtualFS, transaction
from entangled.errors.user import UserError

from pathlib import Path

import pytest


fs = VirtualFS.from_dict({
    "a.md": """
This code block is indented:

    ``` {.python}
    hello

    goodbye
    ```

Note the lack of indentation due to a blank line.
""".lstrip(),

    "indent_error_1.md": """
This code is indented, but contains a line that is not correctly indented:

    ``` {.python}
hello
    ```
""".lstrip(),

    "indent_error_2.md": """
This code is indented, but the closing fence indent doesn't match the opening:

    ``` {.python}
    hello
      ```

This should raise an `unexpected end of file`.
""".lstrip(),

    "indent_error_3.md": """
This code is indented, but the closing fence indent doesn't match the opening:

    ``` {.python}
    hello
  ```

This should raise an `indentation error`.
"""})


def test_indentation():
    doc = Document()
    with transaction(fs=fs) as t:
        doc.load_source(t, Path("a.md"))
        ref = doc.content[Path("a.md")][1]
        assert isinstance(ref, ReferenceId)
        assert doc.reference_map[ref].indent == "    "

        assert doc.source_text(Path("a.md"))[0] == fs[Path("a.md")].content

        for i in range(1, 4):
            with pytest.raises(UserError):
                doc.load_source(t, Path(f"indent_error_{i}.md"))

