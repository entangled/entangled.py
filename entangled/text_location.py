from dataclasses import dataclass


@dataclass
class TextLocation:
    filename: str
    line_number: int = 0

    def __str__(self):
        return f"{self.filename}:{self.line_number}"
