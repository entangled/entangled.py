from dataclasses import dataclass
from pathlib import PurePath


@dataclass
class TextLocation:
    filename: PurePath
    line_number: int = 0

    def __str__(self):
        return f"{self.filename}:{self.line_number}"
