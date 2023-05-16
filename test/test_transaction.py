from pathlib import Path

from entangled.transaction import Transaction, Create, Write, Delete
from entangled.filedb import file_db
from entangled.utility import pushd


def test_transaction(tmp_path: Path):
    with pushd(tmp_path):
        with file_db() as db:
            t = Transaction(db)
            t.write(Path("a"), "hello", [])
            t.write(Path("b"), "goodbye", [Path("a")])

            assert all(isinstance(a, Create) for a in t.actions)
            t.run()
            assert Path("a").exists()
            assert Path("b").exists()
        
        with open(Path("a"), "w") as f:
            f.write("ciao")

        with file_db() as db:
            assert Path("a") in db
            assert Path("b") in db
            assert list(db.changed()) == [Path("a")]

            t = Transaction(db)
            t.write(Path("b"), "goodbye", [])
            assert t.actions == []

            t.write(Path("a"), "buongiorno", [])
            assert isinstance(t.actions[0], Write)
            assert not t.all_ok()

        with file_db() as db:
            t = Transaction(db)
            t.write(Path("a"), "goodbye", [])
            assert isinstance(t.actions[0], Write)
            t.clear_orphans()
            assert isinstance(t.actions[1], Delete)
            t.run()
            assert not Path("b").exists()

