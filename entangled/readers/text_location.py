from dataclasses import dataclass
from pathlib import PurePath
from typing import override


@dataclass
class TextLocation:
    """
    A dataclass to indicate the origin of a line. Because this is only used for
    interfacing with humans, the filename is stored as a string, and line numbers
    start at one.
    """
    filename: PurePath
    line_number: int = 1

    def increment(self):
        self.line_number += 1

    @override
    def __str__(self):
        return f"{self.filename}:{self.line_number}"
