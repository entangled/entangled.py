from dataclasses import dataclass
from collections.abc import Generator


@dataclass
class Builder[T, U]:
    parent: Generator[T, None, U]
    result: U | None = None

    def __iter__(self) -> Generator[T, None, U]:
        self.result = yield from self.parent
        return self.result
