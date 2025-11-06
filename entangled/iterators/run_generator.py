from collections.abc import Generator
from typing import cast


def run_generator[O, R](g: Generator[O, None, R]) -> tuple[list[O], R]:
    result: R | None = None

    def h() -> Generator[O]:
        nonlocal result
        result = yield from g

    out = list(h())

    return out, cast(R, result)
