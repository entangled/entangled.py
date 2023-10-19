from pathlib import Path
from entangled.loom.target import Target


def test_target_parsing():
    t1 = Target.from_str("phony(all)")
    assert t1.is_phony()
    t2 = Target.from_str("blah")
    assert t2.is_path()
    assert t2.path == Path("blah")

