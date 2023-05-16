from typing import Optional, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import contextmanager
from enum import Enum

from .utility import cat_maybes
from .filedb import FileDB, stat, file_db
from .error import InternalError


@dataclass
class Action:
    target: Path

    def conflict(self, _: FileDB) -> Optional[str]:
        """Indicate wether the action might have conflicts. This could be
        inconsistency in the modification times of files, or overwriting
        a file that is not managed by Entangled."""
        raise NotImplementedError()

    def run(self, _: FileDB):
        """Run the action, if `interact` is `True` then confirmation is
        asked in case of a conflict."""
        raise NotImplementedError()


@dataclass
class Create(Action):
    content: str
    sources: list[Path]

    def conflict(self, _) -> Optional[str]:
        if self.target.exists():
            return f"{self.target} already exists and is not managed by Entangled"
        return None

    def run(self, db: FileDB):
        with open(self.target, "w") as f:
            f.write(self.content)
        db.update(self.target)
        if self.sources != []:
            db.managed.add(self.target)

    def __str__(self):
        return f"create `{self.target}`"


@dataclass
class Write(Action):
    content: str
    sources: list[Path]

    def conflict(self, db: FileDB) -> Optional[str]:
        st = stat(self.target)
        if st != db[self.target]:
            return (
                f"{self.target} seems to have changed outside the control of Entangled"
            )
        newest_src = max(stat(s) for s in self.sources)
        if st > newest_src:
            return f"inconsistent modification times: {self.target} seems to be newer than {newest_src.path}"
        return None

    def run(self, db: FileDB):
        with open(self.target, "w") as f:
            f.write(self.content)
        db.update(self.target)

    def __str__(self):
        return f"write `{self.target}`"


@dataclass
class Delete(Action):
    def conflict(self, db: FileDB) -> Optional[str]:
        st = stat(self.target)
        if st != db[self.target]:
            return (
                f"{self.target} seems to have changed outside the control of Entangled"
            )
        return None

    def run(self, db: FileDB):
        self.target.unlink()
        parent = self.target.parent
        while list(parent.iterdir()) == []:
            parent.rmdir()
            parent = parent.parent
        del db[self.target]

    def __str__(self):
        return f"delete `{self.target}`"


@dataclass
class Transaction:
    db: FileDB
    actions: list[Action] = field(default_factory=list)
    passed: set[Path] = field(default_factory=set)

    def write(self, path: Path, content: str, sources: list[Path]):
        if path in self.passed:
            raise InternalError("Path is being written to twice", [path])
        self.passed.add(path)
        if path not in self.db:
            self.actions.append(Create(path, content, sources))
        elif not self.db.check(path, content):
            self.actions.append(Write(path, content, sources))

    def clear_orphans(self):
        orphans = self.db.managed - self.passed
        for p in orphans:
            self.actions.append(Delete(p))

    def check_conflicts(self) -> list[str]:
        return list(cat_maybes(a.conflict(self.db) for a in self.actions))

    def all_ok(self) -> bool:
        return all(a.conflict(self.db) is None for a in self.actions)

    def print_plan(self):
        for a in self.actions:
            print(a)
        for c in self.check_conflicts():
            print(c)

    def run(self):
        for a in self.actions:
            a.run(self.db)


class TransactionMode(Enum):
    SHOW = 1
    FAIL = 2
    CONFIRM = 3
    FORCE = 4


@contextmanager
def transaction(mode: TransactionMode = TransactionMode.FAIL):
    with file_db() as db:
        tr = Transaction(db)

        yield tr

        tr.print_plan()

        match mode:
            case TransactionMode.SHOW:
                return
            case TransactionMode.FAIL:
                if not tr.all_ok():
                    print("conflicts found, breaking off")
                    return
            case TransactionMode.CONFIRM:
                if not tr.all_ok():
                    reply = input("Ok to continue? (y/n) ")
                    if not (reply == "y" or reply == "yes"):
                        return
            case TransactionMode.FORCE:
                print("conflicts found, but continuing anyway")

        tr.run()