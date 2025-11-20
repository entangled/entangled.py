from entangled.interface import Document
from entangled.io import VirtualFS, transaction
import logging
from pathlib import Path

fs = VirtualFS.from_dict({
    "brainfuck.md": """
``` {.brainfuck #hello-world}
>++++++++[<+++++++++>-]<.>++++[<+++++++>-]<+.+++++++..+++.>>++++++[<+++++++>-]<+
+.------------.>++++++[<+++++++++>-]<+.<.+++.------.--------.>>>++++[<++++++++>-
]<+.
```
""".strip()})


def test_unknown_language(caplog):
    doc = Document()
    with transaction(fs=fs) as t:
        with caplog.at_level(logging.WARNING):
            doc.load_source(t, Path("brainfuck.md"))
            assert "language `brainfuck` unknown" in caplog.text

