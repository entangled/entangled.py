from entangled.commands import tangle, stitch
from entangled.markdown_reader import read_markdown_string, read_markdown_file
from entangled.code_reader import CodeReader
from entangled.errors.user import IndentationError

from contextlib import chdir
from pathlib import Path, PurePath
from time import sleep

import pytest

from entangled.tangle import tangle_ref

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


def test_code_indentation():
    refs, _ = read_markdown_string(md_source, Path("test.md"))
    source, _ = tangle_ref(refs, "hello.scm")
    assert source == scm_output1
    for errs in [scm_changed1, scm_changed2, scm_changed3]:
        with pytest.raises(IndentationError):
            _ = CodeReader(PurePath("-"), refs).run(errs)


md_source_error = """
  ``` {.scheme file=hello.scm}
(display "hello") (newline)
```
"""


def test_md_indentation():
    with pytest.raises(IndentationError):
        read_markdown_string(md_source_error)
