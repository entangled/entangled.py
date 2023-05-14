from typing import Iterable, Self, Optional
from dataclasses import dataclass
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime

import json
import hashlib
import os

from .utility import normal_relative
from .filedb import FileDB, stat


class Action(ABC):
    @abstractmethod
    def conflict(self, db: FileDB) -> Optional[str]:
        """Indicate wether the action might have conflicts. This could be
        inconsistency in the modification times of files, or overwriting
        a file that is not managed by Entangled."""
        ...

    @abstractmethod
    def run(self):
        """Run the action, if `interact` is `True` then confirmation is
        asked in case of a conflict."""
        ...


@dataclass
class Create(Action):
    target: Path
    content: str
    sources: list[Path]

    def conflict(self, _) -> Optional[str]:
        if self.target.exists():
            return f"{self.target} already exists and is not managed by Entangled"
        return None
    
    def run(self):
        with open(self.target, "w") as f:
            f.write(self.content)

@dataclass
class Write(Action):
    target: Path
    content: str
    sources: list[Path]

    def conflict(self, db: FileDB) -> Optional[str]:
        st = stat(self.target)
        if st != db[self.target]:
            return f"{self.target} seems to have changed outside the control of Entangled"
        newest_src = max(stat(s) for s in self.sources)
        if st > newest_src:
            return f"inconsistent modification times: {self.target} seems to be newer than {newest_src.path}"
        return None
    
    def run(self):
        with open(self.target, "w") as f:
            f.write(self.content)



@dataclass
class Delete(Action):
    target: Path

    def conflict(self, db: FileDB) -> Optional[str]:
        st = stat(self.target)
        if st != db[self.target]:
            return f"{self.target} seems to have changed outside the control of Entangled"
        return None
    
    def run(self):
        self.target.unlink()
        parent = self.target.parent
        while list(parent.iterdir()) == []:
            parent.rmdir()
            parent = parent.parent



# @dataclass
# class Transaction:
#     pass