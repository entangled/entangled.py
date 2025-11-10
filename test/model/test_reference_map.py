from entangled.model import CodeBlock, ReferenceName, ReferenceId, ReferenceMap
from entangled.model.reference_map import ReferenceMap
from entangled.text_location import TextLocation
from entangled.errors.internal import InternalError
from entangled.model.properties import Attribute

from pathlib import PurePath

import pytest

def mock_code_block() -> CodeBlock:
    return CodeBlock(properties=[], indent="", open_line="", close_line="", source="", origin=TextLocation(PurePath("-"), 0))

def ref(name: str) -> ReferenceName:
    return ReferenceName((), name)

def test_reference_map():
    refs = ReferenceMap()
    assert bool(refs) == False
    r1 = refs.new_id(PurePath("x.md"), ref("a"))
    cb1 = mock_code_block()
    assert r1 not in refs
    refs[r1] = cb1
    assert r1 in refs
    assert refs[r1] is cb1

    with pytest.raises(InternalError):
        refs[r1] = mock_code_block()

    r2 = refs.new_id(PurePath("x.md"), ref("a"))
    refs[r2] = mock_code_block()
    assert r2.ref_count == 1
    r3 = refs.new_id(PurePath("y.md"), ref("a"))
    refs[r3] = mock_code_block()
    assert r3.ref_count == 0
    assert refs.select_by_name(ref("a")) == [r1, r2, r3]

    refs.register_target(PurePath("a.py"), ref("a"))
    assert refs.select_by_target(PurePath("a.py")) == ref("a")

    cb2 = mock_code_block()
    cb2.properties.append(Attribute("file", "b.py"))
    r4 = refs.new_id(PurePath("x.md"), ref("b"))
    refs[r4] = cb2
    assert refs.select_by_target(PurePath("b.py")) == ref("b")

    assert len(refs) == 4
    assert set(refs) == { r1, r2, r3, r4 }

    r5 = refs.new_id(PurePath("x.md"), ref("b"))
    del refs[r5]
    assert len(refs) == 4
    del refs[r4]
    assert len(refs) == 3
    assert r4 not in refs
    
    

