from enum import StrEnum


class DocumentStyle(StrEnum):
    """Document style is a short hand for markdown style and hook settings.

    - `DEFAULT` is the default. We have fenced code blocks with a set of
      attributes attached in curly braces. This setting offers the most
      consistent syntax but is sometimes lacking in support from third-party
      tools.

    - `BASIC` sets a simpler syntax where only the language is passed on the
      same line as the code block fences. All other metadata is to be passed
      using Quatro style attributes.
    """

    DEFAULT = "default"
    BASIC = "basic"
