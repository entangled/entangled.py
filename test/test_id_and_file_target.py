from entangled.config import AnnotationMethod, Config
from entangled.interface import Context, markdown
from entangled.readers import run_reader
from entangled.model import tangle_ref, ReferenceMap, ReferenceName

from functools import partial
from pathlib import PurePath


md_in = """
``` {.rust file=test1.rs #blockid1}
fn main() {
    println!("Hello, World!");
}
```

``` {.rust #blockid2 file=test2.rs}
fn main() {
    println!("Hello, World!");
}
```

``` {.rust #blockid3 file=test3.rs}
fn fac(i: u64) -> u64 {
    result: u64 = 1;
    for j in 1..i {
        result *= j;
    }
    return result;
}
```

``` {.rust #blockid3}
fn main() {
    println!("42! = {}", fac(42));
}
```
"""

result1_out = result2_out = """
fn main() {
    println!("Hello, World!");
}
"""

result3_out = """
fn fac(i: u64) -> u64 {
    result: u64 = 1;
    for j in 1..i {
        result *= j;
    }
    return result;
}
fn main() {
    println!("42! = {}", fac(42));
}
"""

def test_id_and_file_target():
    refs = ReferenceMap()
    _ = run_reader(partial(markdown, Context(), refs), md_in)

    content1, _ = tangle_ref(refs, ReferenceName((), "blockid1"), AnnotationMethod.NAKED)
    assert content1.strip() == result1_out.strip()
    content2, _ = tangle_ref(refs, ReferenceName((), "blockid2"), AnnotationMethod.NAKED)
    assert content2.strip() == result2_out.strip()
    content3, _ = tangle_ref(refs, ReferenceName((), "blockid3"), AnnotationMethod.NAKED)
    assert content3.strip() == result3_out.strip()

    assert sorted(refs.targets()) == [PurePath(f"test{i}.rs") for i in range(1, 4)]
    for i in range(1, 4):
        assert refs.select_by_target(PurePath(f"test{i}.rs")) == ReferenceName((), f"blockid{i}")

