from typing import Optional
from dataclasses import dataclass


@dataclass
class Comment:
    """Comment method for a language. For example: `Comment("/*", "*/")` works
    for C/C++ etc, `Comment("#")` works for Python, and so on.
    """

    open: str
    close: Optional[str] = None


@dataclass
class Language:
    """Language information. Given a language we may have any number of short-hands
    to indicate a code block is written in that language. If a language supports
    line directives this can be used to redirect compiler messages directly to the
    markdown files."""

    name: str
    identifiers: list[str]
    comment: Comment
    line_directive: Optional[str] = None


languages = [
    Language("C", ["c", "cpp", "c++"], Comment("/*", "*/")),
    Language("Python", ["python"], Comment("#")),
    Language("Rust", ["rust"], Comment("//")),
    Language("Haskell", ["haskell"], Comment("--")),
    Language(
        "Lisp", ["scheme", "r5rs", "r6rs", "r7rs", "racket", "clojure"], Comment(";")
    ),
    Language("Julia", ["julia"], Comment("#")),
    Language("Java", ["java"], Comment("//")),
    Language("CSS", ["css"], Comment("/*", "*/")),
    Language("Lua", ["lua"], Comment("--")),
    Language("Make", ["make", "makefile"], Comment("#"))
]
