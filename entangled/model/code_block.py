from dataclasses import dataclass

import os

from ..text_location import TextLocation
from ..readers.lines import lines
from ..config.language import Language
from .properties import Property


def indent(prefix: str, text: str) -> str:
    def indent_line(line: str):
        if line.strip() == "" and line.endswith(os.linesep):
            return os.linesep
        if line.strip() == "":
            return ""

        return prefix + line

    return "".join(map(indent_line, lines(text)))


@dataclass
class CodeBlock:
    """
    Contains all distilled information on a codeblock.

    Attributes:
        properties: Id, classes and attributes.
        indent: The indentation prefix.
        open_line: One or more lines preceding the source. When `quatro_attributes`
            are enabled, these attribute lines are appended onto `open_line`.
        close_line: One or more lines after the source content of the code block.
        source: Source code in this code block.
        origin: Original location in markup source.
        language: Detected programming language.
        header: (assumes `file` attribute) Content at the top of the code block
            that should appear before the first comment line at the top of a
            file (shebang or spdx license).
        mode: (assumes `file` attribute) The access mode of the file being
            written as a string in octal numbers. Example: "0755" to make a
            file executable.
        namespace: The namespace of the markup file from which the code block
            was read.
    """
    properties: list[Property]
    indent: str
    open_line: str
    close_line: str
    source: str
    origin: TextLocation
    language: Language | None = None
    header: str | None = None
    mode: int | None = None
    namespace: tuple[str, ...] = ()

    @property
    def text(self) -> str:
        """
        The unindented text that should be identical to the text from which the
        code block was extracted.
        """
        return self.open_line + (self.header or "") + self.source + self.close_line

    @property
    def indented_text(self) -> str:
        """
        The text that should be identical to the text from which the code block was
        extracted, including the indentation.
        """
        return indent(self.indent, self.text)
