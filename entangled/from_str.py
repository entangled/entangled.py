from abc import ABC, abstractmethod
from typing import Self, Any


class FromStr(ABC):
    @abstractmethod
    def to_str(self) -> str:
        ...

    @classmethod
    @abstractmethod
    def from_str(cls, s: str) -> Self:
        ...


def enc_hook(obj: Any) -> str:
    if isinstance(obj, FromStr):
        return obj.to_str()
    else:
        raise NotImplementedError # (f"Object should implement `FromStr`, got: `{type(obj)}`.")


def dec_hook(cls: type, obj: Any) -> Any:
    if issubclass(cls, FromStr) and isinstance(obj, str):
        return cls.from_str(obj)
    else:
        raise NotImplementedError(f"Unsupported type, couldn't decode `{obj}` to `{cls}`.")
