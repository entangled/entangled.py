from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from contextlib import contextmanager
from enum import Enum

import logging
from typing import override

from ..utility import cat_maybes
from ..errors.internal import InternalError

from .stat import Stat, hexdigest
from .virtual import FileCache
from .filedb import FileDB, filedb


@dataclass(frozen=True)
class Conflict:
    target: Path
    description: str

    @override
    def __str__(self):
        return f"`{self.target}` {self.description}"


@dataclass(frozen=True)
class Action(metaclass=ABCMeta):
    target: Path

    @abstractmethod
    def conflict(self, fs: FileCache, db: FileDB) -> Conflict | None:
        """Indicate wether the action might have conflicts. This could be
        inconsistency in the modification times of files, or overwriting
        a file that is not managed by Entangled."""
        ...

    @abstractmethod
    def add_to_db(self, fs: FileCache, db: FileDB):
        """Only perform the corresponding database action."""
        ...

    @abstractmethod
    def run(self, fs: FileCache):
        """Run the action, if `interact` is `True` then confirmation is
        asked in case of a conflict."""
        ...

    def target_stat(self, fs: FileCache) -> Stat | None:
        if self.target not in fs:
            return None
        return fs[self.target].stat


@dataclass(frozen=True)
class WriterBase(Action, metaclass=ABCMeta):
    content: str
    mode: int | None
    sources: list[Path]

    @cached_property
    def content_digest(self) -> str:
        return hexdigest(self.content)

    @override
    def run(self, fs: FileCache):
        fs.write(self.target, self.content, self.mode)


class Create(WriterBase):
    @override
    def conflict(self, fs: FileCache, db: FileDB) -> Conflict | None:
        if self.target in fs:
            if (self.content_digest == fs[self.target].stat.hexdigest):
                return None
            return Conflict(self.target, "not managed by Entangled")
        return None

    @override
    def add_to_db(self, fs: FileCache, db: FileDB):
        return db.create_target(fs, self.target)

    @override
    def __str__(self):
        return f"create `{self.target}`"


class Write(WriterBase):
    @override
    def conflict(self, fs: FileCache, db: FileDB) -> Conflict | None:
        if self.target not in fs:
            return None
        if fs[self.target].stat != db[self.target]:
            return Conflict(self.target, "changed outside the control of Entangled")
        if self.sources:
            if all(fs[s].stat < fs[self.target].stat for s in self.sources):
                return Conflict(self.target, "newer than all of its sources: " + ", ".join(
                    f"`{s}`" for s in set(self.sources)))
        return None

    @override
    def add_to_db(self, fs: FileCache, db: FileDB):
        db.update(fs, self.target)

    @override
    def __str__(self):
        return f"write `{self.target}`"


class Delete(Action):
    @override
    def conflict(self, fs: FileCache, db: FileDB) -> Conflict | None:
        if fs[self.target].stat != db[self.target]:
            return Conflict(self.target, "changed outside the control of Entangled")
        return None

    @override
    def add_to_db(self, fs: FileCache, db: FileDB):
        del db[self.target]

    @override
    def run(self, fs: FileCache):
        del fs[self.target]

    @override
    def __str__(self):
        return f"delete `{self.target}`"


@dataclass
class Transaction:
    """
    Collects a set of file mutations, checking for consistency. All file IO outside of
    the `entangled.io` module should pass through this class, used with the context
    manager function `transaction`.
    """
    db: FileDB
    fs: FileCache = field(default_factory=FileCache)
    updates: list[Path] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    passed: set[Path] = field(default_factory=set)

    def update(self, path: Path):
        self.updates.append(path)

    def write(self, path: Path, content: str, sources: list[Path], mode: int | None = None):
        if path in self.passed:
            raise InternalError("Path is being written to twice", [path])
        self.passed.add(path)
        if path not in self.db:
            logging.debug("creating target `%s`", path)
            self.actions.append(Create(path, content, mode, sources))
        elif not self.db.check(path, content):
            logging.debug("target `%s` changed", path)
            self.actions.append(Write(path, content, mode, sources))
        else:
            logging.debug("target `%s` unchanged", path)

    def clear_orphans(self):
        orphans = self.db.managed_files - self.passed
        if not orphans:
            return

        logging.info("orphans found: `%s`", ", ".join(map(str, orphans)))
        for p in orphans:
            self.actions.append(Delete(p))

    def check_conflicts(self) -> list[Conflict]:
        return list(cat_maybes(a.conflict(self.fs, self.db) for a in self.actions))

    def all_ok(self) -> bool:
        return all(a.conflict(self.fs, self.db) is None for a in self.actions)

    def print_plan(self):
        if not self.actions:
            logging.info("Nothing to be done.")
        for a in self.actions:
            logging.info(str(a))
        for c in self.check_conflicts():
            logging.warning(str(c))

    def run(self):
        for a in self.actions:
            a.run(self.fs)
            a.add_to_db(self.fs, self.db)
        for f in self.updates:
            self.db.update(self.fs, f)

    def updatedb(self):
        for a in self.actions:
            a.add_to_db(self.fs, self.db)
        for f in self.updates:
            self.db.update(self.fs, f)


class TransactionMode(Enum):
    """
    Selects the mode of transaction:

    - `SHOW` only show what would be done
    - `FAIL` fail with an error message if any conflicts are found
    - `CONFIRM` in the evennt of conflicts, ask the user for confirmation
    - `FORCE` print a warning on conflicts but execute anyway
    - `RESETDB` recreate the filedb in case it got corrupted
    """
    SHOW = 1
    FAIL = 2
    CONFIRM = 3
    FORCE = 4
    RESETDB = 5


@contextmanager
def transaction(mode: TransactionMode = TransactionMode.FAIL):
    with filedb(writeonly = (mode == TransactionMode.RESETDB)) as db:
        if mode == TransactionMode.RESETDB:
            db.clear()

        tr = Transaction(db)

        logging.debug("Open transaction")
        yield tr

        tr.print_plan()

        match mode:
            case TransactionMode.SHOW:
                logging.info("nothing is done")
                return

            case TransactionMode.RESETDB:
                logging.info("rebuilding database")
                tr.updatedb()
                return

            case TransactionMode.FAIL:
                if not tr.all_ok():
                    logging.error(
                        "conflicts found, breaking off (use `--force` to run anyway)"
                    )
                    return

            case TransactionMode.CONFIRM:
                if not tr.all_ok():
                    reply = input("Ok to continue? (y/n) ")
                    if not (reply == "y" or reply == "yes"):
                        return

            case TransactionMode.FORCE:
                logging.warning("conflicts found, but continuing anyway")

        logging.debug("Executing transaction")
        tr.run()
