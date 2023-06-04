from pathlib import Path
import pytest

from entangled.tangle import tangle_ref
from entangled.markdown_reader import MarkdownReader
from entangled.errors.user import CyclicReference
from entangled.document import AnnotationMethod


md_source = """
This should raise a `CyclicReference` error.

``` {.python #hello}
<<hello>>
```

So should this:

``` {.python #phobos}
<<deimos>>
```

``` {.python #deimos}
<<phobos>>
```

also when tangling from something else:

``` {.python #mars}
<<phobos>>
```

What should not throw an error is doubling a reference:

``` {.python #helium}
<<electron>>
<<electron>>
```

``` {.python #electron}
negative charge
```
"""


def test_cycles():
    mr = MarkdownReader("-")
    mr.run(md_source)
    refs = mr.reference_map

    with pytest.raises(CyclicReference):
        tangle_ref(refs, "hello")

    with pytest.raises(CyclicReference):
        result, _ = tangle_ref(refs, "phobos")
        print(result)

    try:
        tangle_ref(refs, "mars")
    except CyclicReference as e:
        assert e.cycle == ["mars", "phobos", "deimos"]

    result, _ = tangle_ref(refs, "helium", AnnotationMethod.NAKED)
    assert result == "negative charge\nnegative charge"
