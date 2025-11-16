from pathlib import PurePath
import pytest

from entangled.readers.yaml_header import read_yaml_header, get_config
from entangled.iterators import numbered_lines
from entangled.errors.user import ParseError, UserError
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

input_not_an_object = """
---
[1, 2, 3]
---
""".strip()

input_invalid = """
---
entangled:
    no_version_given: 0
---
""".strip()


def get_yaml_header(input: str) -> object:
    path = PurePath("-")
    result = None

    def reader() -> MarkdownStream[object]:
         nonlocal result
         result = yield from read_yaml_header(numbered_lines(path, input))
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

    with pytest.raises(UserError):
        _ = get_config(get_yaml_header(input_not_an_object))

    with pytest.raises(UserError):
        _ = get_config(get_yaml_header(input_invalid))

