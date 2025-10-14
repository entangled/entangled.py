from contextlib import chdir
from pathlib import Path

from entangled.io.transaction import Transaction, Create, Write, Delete
from entangled.io.filedb import filedb
from entangled.io.virtual import FileCache


def test_transaction(tmp_path: Path):
    with chdir(tmp_path):
        fs = FileCache()

        with filedb() as db:
            t = Transaction(db)
            t.write(Path("a"), "hello", [])
            t.write(Path("b"), "goodbye", [Path("a")])

            assert all(isinstance(a, Create) for a in t.actions)
            t.run()
            assert Path("a").exists()
            assert Path("b").exists()

        with open(Path("a"), "w") as f:
            _ = f.write("ciao")

        fs.reset()
        with filedb() as db:
            assert Path("a") in db
            assert Path("b") in db
            assert list(db.changed_files(fs)) == [Path("a")]

            t = Transaction(db)
            t.write(Path("b"), "goodbye", [])
            assert t.actions == []

            t.write(Path("a"), "buongiorno", [])
            assert isinstance(t.actions[0], Write)
            assert not t.all_ok()

        with filedb() as db:
            t = Transaction(db)
            t.write(Path("a"), "goodbye", [])
            assert isinstance(t.actions[0], Write)
            t.clear_orphans()
            assert isinstance(t.actions[1], Delete)
            t.run()
            assert not Path("b").exists()
