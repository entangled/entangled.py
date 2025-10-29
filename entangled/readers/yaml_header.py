from ..document import PlainText
from ..errors.user import ParseError
from .types import InputStream, MarkdownStream

import yaml


def read_yaml_header(input: InputStream) -> MarkdownStream[object]:
    """
    Reads the YAML header that can be found at the top of a Markdown document.
    """
    if not input:
        return None

    pos, line = input.peek()
    if line.rstrip() == "---":
        _ = next(input)
        yield PlainText(line)
    else:
        return None

    raw_header = ""
    for pos, line in input:
        if line.rstrip() == "---":
            try:
                header = yaml.safe_load(raw_header)  # pyright: ignore[reportAny]
            except yaml.YAMLError as e:
                raise ParseError(pos, str(e))

            yield PlainText(raw_header)
            yield PlainText(line)
            return header  # pyright: ignore[reportAny]

        else:
            raw_header += line

    raise ParseError(pos, "unterminated YAML header")
