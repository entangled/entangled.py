from typing import Optional, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import contextmanager
from enum import Enum

import os
import tempfile
import logging

try:
    import rich

    WITH_RICH = True
except ImportError:
    WITH_RICH = False

from .utility import cat_maybes
from .filedb import FileDB, stat, file_db, hexdigest
from .errors.internal import InternalError


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
    mode: int | None

    def conflict(self, _) -> Optional[str]:
        if self.target.exists():
            # Check if file contents are the same as what we want to write or is empty
            # then it is safe to take ownership.
            md_stat = stat(self.target)
            fileHexdigest = md_stat.hexdigest
            contentHexdigest = hexdigest(self.content)
            if (contentHexdigest == fileHexdigest) or (md_stat.size == 0):
                return None
            return f"{self.target} is not managed by Entangled"
        return None

    def run(self, db: FileDB):
        self.target.parent.mkdir(parents=True, exist_ok=True)
        # Write to tmp file then replace with file name
        tmp_dir = Path() / ".entangled" / "tmp"
        tmp_dir.mkdir(exist_ok=True, parents=True)
        with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=tmp_dir) as f:
            f.write(self.content)
            # Flush and sync contents to disk
            f.flush()
            if self.mode is not None:
                os.chmod(f.name, self.mode)
            os.fsync(f.fileno())
        os.replace(f.name, self.target)
        db.update(self.target, self.sources)
        if self.sources != []:
            db.managed.add(self.target)

    def __str__(self):
        return f"create `{self.target}`"


@dataclass
class Write(Action):
    content: str
    sources: list[Path]
    mode: int | None

    def conflict(self, db: FileDB) -> Optional[str]:
        st = stat(self.target)
        if st != db[self.target]:
            return f"`{self.target}` seems to have changed outside the control of Entangled"
        if self.sources:
            newest_src = max(stat(s) for s in self.sources)
            if st > newest_src:
                return f"`{self.target}` seems to be newer than `{newest_src.path}`"
        return None

    def run(self, db: FileDB):
        # Write to tmp file then replace with file name
        tmp_dir = Path() / ".entangled" / "tmp"
        tmp_dir.mkdir(exist_ok=True, parents=True)
        with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=tmp_dir) as f:
            f.write(self.content)
            # Flush and sync contents to disk
            f.flush()
            if self.mode is not None:
                os.chmod(f.name, self.mode)
            os.fsync(f.fileno())
        os.replace(f.name, self.target)
        db.update(self.target, self.sources)

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
            self.actions.append(Create(path, content, sources, mode))
        elif not self.db.check(path, content):
            logging.debug("target `%s` changed", path)
            self.actions.append(Write(path, content, sources, mode))
        else:
            logging.debug("target `%s` unchanged", path)

    def clear_orphans(self):
        orphans = self.db.managed - self.passed
        if not orphans:
            return

        logging.info("orphans found: `%s`", ", ".join(map(str, orphans)))
        for p in orphans:
            self.actions.append(Delete(p))

    def check_conflicts(self) -> list[str]:
        return list(cat_maybes(a.conflict(self.db) for a in self.actions))

    def all_ok(self) -> bool:
        return all(a.conflict(self.db) is None for a in self.actions)

    def print_plan(self):
        if not self.actions:
            logging.info("Nothing to be done.")
        for a in self.actions:
            logging.info(str(a))
        for c in self.check_conflicts():
            logging.warning(str(c))

    def run(self):
        for a in self.actions:
            a.run(self.db)
        for f in self.updates:
            self.db.update(f)


class TransactionMode(Enum):
    SHOW = 1
    FAIL = 2
    CONFIRM = 3
    FORCE = 4


@contextmanager
def transaction(mode: TransactionMode = TransactionMode.FAIL):
    with file_db() as db:
        tr = Transaction(db)

        logging.debug("Open transaction")
        yield tr

        tr.print_plan()

        match mode:
            case TransactionMode.SHOW:
                logging.info("nothing is done")
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
