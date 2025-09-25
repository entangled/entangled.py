from dataclasses import dataclass
from pathlib import PurePath
from typing import override

@dataclass
class TextLocation:
    filename: PurePath
    line_number: int = 0

    @override
    def __str__(self) -> str:
        return f"{self.filename}:{self.line_number}"
