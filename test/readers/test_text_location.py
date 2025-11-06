from pathlib import PurePath
from entangled.text_location import TextLocation


def test_text_location():
    pos = TextLocation(PurePath("foo"), 4)
    assert str(pos) == "foo:4"
    pos.increment()
    assert str(pos) == "foo:5"
    pos.increment()
    assert pos.filename == PurePath("foo")
    assert pos.line_number == 6
