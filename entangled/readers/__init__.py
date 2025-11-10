from pathlib import PurePath

from .markdown import markdown
from .code import read_top_level as code
from ..iterators import numbered_lines, run_generator
from .types import Reader


def run_reader[O, T](reader: Reader[O, T], inp: str, filename: str = "-") -> tuple[list[O], T]:
    return run_generator(reader(numbered_lines(PurePath(filename), inp)))


__all__ = ["markdown", "code", "run_reader"]

