from pathlib import PurePath

from .yaml_header import read_yaml_header
from .markdown import process_token, collect_plain_text, raw_markdown
from .code import read_top_level as code
from ..iterators import numbered_lines, run_generator
from .types import Reader, InputStream


def run_reader[O, T](reader: Reader[O, T], inp: str, filename: str = "-") -> tuple[list[O], T]:
    return run_generator(reader(numbered_lines(PurePath(filename), inp)))


__all__ = ["read_yaml_header", "process_token", "collect_plain_text", "raw_markdown",
           "code", "run_reader", "InputStream"]

