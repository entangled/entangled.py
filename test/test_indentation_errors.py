from entangled.commands import tangle, stitch
from entangled.markdown_reader import read_markdown_string, read_markdown_file
from entangled.code_reader import CodeReader
from entangled.errors.user import IndentationError

from contextlib import chdir
from pathlib import Path
from time import sleep

import pytest

md_source = """
``` {.scheme file=hello.scm}
(display "hello") (newline)

(let (x 42)
  <<print-x>>
)
```

``` {.scheme #print-x}
(display x)
  <<newline>>
```

``` {.scheme #newline}
(newline)
```
"""

scm_output1 = """; ~/~ begin <<test.md#hello.scm>>[init]
(display "hello") (newline)

(let (x 42)
  ; ~/~ begin <<test.md#print-x>>[init]
  (display x)
    ; ~/~ begin <<test.md#newline>>[init]
    (newline)
    ; ~/~ end
  ; ~/~ end
)
; ~/~ end"""


scm_changed1 = """; ~/~ begin <<test.md#hello.scm>>[init]
(display "goodbye") (newline)

(let (x 42)
  ; ~/~ begin <<test.md#print-x>>[init]
  (display x)
    ; ~/~ begin <<test.md#newline>>[init]
    (newline)
    ; ~/~ end
  ; ~/~ end
)
    ; ~/~ end"""


scm_changed2 = """; ~/~ begin <<test.md#hello.scm>>[init]
(display "hello") (newline)

(let (x 42)
  ; ~/~ begin <<test.md#print-x>>[init]
  (display x)
;   ; ~/~ begin <<test.md#newline>>[init]
    (newline)
    ; ~/~ end
  ; ~/~ end
)
; ~/~ end"""


scm_changed3 = """; ~/~ begin <<test.md#hello.scm>>[init]
(display "hello") (newline)

(let (x 42)
  ; ~/~ begin <<test.md#print-x>>[init]
  (display x)
    ; ~/~ begin <<test.md#newline>>[init]
  (newline)
    ; ~/~ end
  ; ~/~ end
)
; ~/~ end"""


def test_code_indentation(tmp_path):
    with chdir(tmp_path):
        src = Path("test.md")
        src.write_text(md_source)
        sleep(0.1)
        tangle()
        sleep(0.1)
        tgt = Path("hello.scm")
        assert tgt.exists() and tgt.read_text() == scm_output1
        refs, _ = read_markdown_file(src)

        tgt.write_text(scm_changed1)
        sleep(0.1)
        with pytest.raises(IndentationError):
            CodeReader(str(tgt), refs).run(tgt.read_text())
        stitch()
        sleep(0.1)
        assert src.read_text() == md_source

        for errs in [scm_changed1, scm_changed2, scm_changed3]:
            with pytest.raises(IndentationError):
                CodeReader("-", refs).run(errs)


md_source_error = """
  ``` {.scheme file=hello.scm}
(display "hello") (newline)
```
"""


def test_md_indentation():
    with pytest.raises(IndentationError):
        read_markdown_string(md_source_error)
