from entangled.loom.file_task import Phony

# from entangled.parsing import


def test_phony_parsing():
    x, _ = Phony.read("phony(all)")
    assert x == Phony("all")
    assert str(x) == "phony(all)"
