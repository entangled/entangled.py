from enum import StrEnum


class NamespaceDefault(StrEnum):
    """Default namespace behaviour.

    - `GLOBAL` is the default. Identifiers are all collected into the global
      namespace.

    - `PRIVATE` means that identifiers are only accessible within the same file.
    """

    GLOBAL = "global"
    PRIVATE = "private"
