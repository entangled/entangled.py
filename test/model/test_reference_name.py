from entangled.model.reference_name import ReferenceName


def test_reference_name():
    n1 = ReferenceName.from_str("a")
    assert n1.namespace == ()
    assert n1.name == "a"
    assert str(n1) == "a"

    n2 = ReferenceName.from_str("a::b::c")
    assert n2.namespace == ("a", "b")
    assert n2.name == "c"
    assert str(n2) == "a::b::c"

    assert hash(n1) != hash(n2)

