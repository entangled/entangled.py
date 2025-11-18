from functools import partial
import pytest

from entangled.model import ReferenceMap, ReferenceName
from entangled.model.tangle import tangle_ref, CyclicReference
from entangled.readers import markdown, run_reader
from entangled.config import Config, AnnotationMethod


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



@pytest.mark.timeout(5)
def test_cycles():
    refs = ReferenceMap()
    _ = run_reader(partial(markdown, Config(), refs), md_source)

    with pytest.raises(CyclicReference):
        _ = tangle_ref(refs, ReferenceName((), "hello"), AnnotationMethod.NAKED)

    with pytest.raises(CyclicReference):
        _ = tangle_ref(refs, ReferenceName((), "phobos"), AnnotationMethod.NAKED)

    try:
        _ = tangle_ref(refs, ReferenceName((), "mars"), AnnotationMethod.NAKED)
    except CyclicReference as e:
        assert e.cycle == ["mars[0]", "phobos[0]", "deimos[0]"]
        assert all(planet in str(e) for planet in ["mars", "phobos", "deimos"])

    result, _ = tangle_ref(refs, ReferenceName((), "helium"), AnnotationMethod.NAKED)
    assert result == "negative charge\nnegative charge\n"

