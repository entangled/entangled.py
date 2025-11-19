from entangled.config import Config, AnnotationMethod
from entangled.readers import run_reader
from entangled.model import ReferenceMap, ReferenceName, ReferenceId, tangle_ref
from entangled.model.tangle import MissingLanguageError, MissingReference
from entangled.interface import Context, markdown

from pathlib import PurePath
from functools import partial

import pytest
import textwrap


input1_md = """
``` {.python #f}
def f(n):
    <<f-condition>>
```

``` {.python #f-condition}
if n == 0:
    <<f-base-case>>
else:
    <<f-recursion>>
```

``` {.python #f-base-case}
return 1
```

``` {.python #f-recursion}
return n * f(n - 1)
```

``` {.python #g}
print('a')
```

``` {.python #g}
print('b')
```

``` {.python #g}
print('c')
```

``` {.python #main}
#!/usr/bin/python

if __name__ == "__main__":
    <<g>>
```

``` {.python #e}
<<not-here>>
```
""".lstrip()


naked_tangle_1 = """
def f(n):
    if n == 0:
        return 1
    else:
        return n * f(n - 1)
""".lstrip()


annot_tangle_1 = """
# ~/~ begin <<-#f>>[init]
def f(n):
    # ~/~ begin <<-#f-condition>>[init]
    if n == 0:
        # ~/~ begin <<-#f-base-case>>[init]
        return 1
        # ~/~ end
    else:
        # ~/~ begin <<-#f-recursion>>[init]
        return n * f(n - 1)
        # ~/~ end
    # ~/~ end
# ~/~ end
""".lstrip()


def ref(name: str, num: int = 0) -> ReferenceId:
    return ReferenceId(ReferenceName((), name), PurePath("-"), num)


def test_nested_indent():
    refs = ReferenceMap()
    _ = run_reader(partial(markdown, Context(), refs), input1_md)
    n1, _ = tangle_ref(refs, ReferenceName((), "f"), AnnotationMethod.NAKED)
    assert n1 == naked_tangle_1
    n1_annot, _ = tangle_ref(refs, ReferenceName((), "f"), AnnotationMethod.STANDARD)
    print(n1_annot)
    assert n1_annot == annot_tangle_1


def test_missing_language():
    # this should never happen, but the data model allows for it
    refs = ReferenceMap()
    _ = run_reader(partial(markdown, Context(), refs), input1_md)
    code_block = refs[ref("f-condition")]
    code_block.language = None

    with pytest.raises(MissingLanguageError) as exc:
        _ = tangle_ref(refs, ReferenceName((), "f"), AnnotationMethod.STANDARD)

    assert "-:6" in str(exc.value)


def test_sequence():
    refs = ReferenceMap()
    _ = run_reader(partial(markdown, Context(), refs), input1_md)
    g1, _ = tangle_ref(refs, ReferenceName((), "g"), AnnotationMethod.NAKED)
    assert g1 == "print('a')\nprint('b')\nprint('c')\n"
    g2, _ = tangle_ref(refs, ReferenceName((), "main"), AnnotationMethod.NAKED)
    assert g2 == "#!/usr/bin/python\n\nif __name__ == \"__main__\":\n" + textwrap.indent(g1, "    ")

    g2_annot, _ = tangle_ref(refs, ReferenceName((), "main"))
    assert g2_annot.startswith("#!/usr/bin/python\n")


def test_absent_ref():
    refs = ReferenceMap()
    _ = run_reader(partial(markdown, Context(), refs), input1_md)

    with pytest.raises(KeyError):
        _ = tangle_ref(refs, ReferenceName((), "z"))

    with pytest.raises(MissingReference) as exc:
        _ = tangle_ref(refs, ReferenceName((), "e"))

    assert "not-here" in str(exc.value)
