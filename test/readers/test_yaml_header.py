from pathlib import PurePath
import logging
import pytest

from entangled.readers.yaml_header import read_yaml_header
from entangled.readers.lines import lines
from entangled.errors.user import ParseError
from entangled.readers.types import MarkdownStream


input_correct = """---
title: hello
---

more content
"""

input_non_terminating = """---
title: hello

there's no end to this header
"""

input_no_header = """
Nothing to see here.
"""

input_not_on_top = """

---
title: hello
---

should this header be parsed or not?
"""


input_invalid_yaml = """---
}
---
"""


def get_yaml_header(input: str) -> object:
    path = PurePath("-")
    result = None

    def reader() -> MarkdownStream[object]:
         nonlocal result
         result = yield from read_yaml_header(lines(path, input))
         return

    def run():
        for _ in reader():
            pass

    run()
    return result


def test_read_yaml_header():
    assert get_yaml_header(input_correct) == { "title": "hello" }
    assert get_yaml_header(input_no_header) is None
    assert get_yaml_header(input_not_on_top) is None

    with pytest.raises(ParseError):
        _ = get_yaml_header(input_invalid_yaml)

    with pytest.raises(ParseError):
        _ = get_yaml_header(input_non_terminating)
