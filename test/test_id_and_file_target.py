from entangled.markdown_reader import MarkdownReader
from entangled.tangle import tangle_ref, AnnotationMethod

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
    mr = MarkdownReader("-")
    mr.run(md_in)

    content1, _ = tangle_ref(mr.reference_map, "blockid1", AnnotationMethod.NAKED)
    assert content1.strip() == result1_out.strip()
    content2, _ = tangle_ref(mr.reference_map, "blockid2", AnnotationMethod.NAKED)
    assert content2.strip() == result2_out.strip()
    content3, _ = tangle_ref(mr.reference_map, "blockid3", AnnotationMethod.NAKED)
    assert content3.strip() == result3_out.strip()

    assert mr.reference_map.targets == {"test1.rs", "test2.rs", "test3.rs"}
    for i in range(1, 4):
        ref = f"test{i}.rs"
        bid = f"blockid{i}"
        c, _ = tangle_ref(mr.reference_map, ref, AnnotationMethod.NAKED)
        d, _ = tangle_ref(mr.reference_map, ref, AnnotationMethod.NAKED)
        assert c == d
