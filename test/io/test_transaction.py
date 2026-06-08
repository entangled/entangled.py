from contextlib import chdir
from pathlib import Path
from time import sleep

from entangled.io.transaction import Transaction, Create, Write, Delete
from entangled.io.filedb import filedb
from entangled.io.virtual import FileCache


def test_transaction(tmp_path: Path):
    with chdir(tmp_path):
        fs = FileCache()

        with filedb(fs=fs) as db:
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
        print(Path(".entangled/filedb.json").read_text())
        with filedb(fs=fs) as db:
            assert Path("a") in db
            assert Path("b") in db
            assert list(db.changed_files(fs)) == [Path("a")]

            t = Transaction(db)
            t.write(Path("b"), "goodbye", [])
            assert t.actions == []

            t.write(Path("a"), "buongiorno", [])
            assert isinstance(t.actions[0], Write)
            assert not t.all_ok()

        with filedb(fs=fs) as db:
            t = Transaction(db)
            t.write(Path("a"), "goodbye", [])
            assert isinstance(t.actions[0], Write)
            t.clear_orphans()
            assert isinstance(t.actions[1], Delete)
            t.run()
            assert not Path("b").exists()


def test_changing_dependencies(tmp_path: Path):
    """Regression test for issue #96: when a target no longer depends on one of
    its former sources, Entangled should still be able to update it. The target
    is then necessarily newer than its remaining sources, but as long as it was
    not edited outside of Entangled (i.e. it matches the filedb), overwriting it
    is safe and should not be reported as a conflict."""
    with chdir(tmp_path):
        fs = FileCache()

        # the source files are older than anything generated from them
        with open("input1", "w") as f:
            _ = f.write("source one")
        with open("input2", "w") as f:
            _ = f.write("source two")
        sleep(0.01)

        # first run: `output` is generated from both inputs
        with filedb(fs=fs) as db:
            t = Transaction(db)
            t.write(Path("output"), "from one and two",
                    [Path("input1"), Path("input2")])
            assert isinstance(t.actions[0], Create)
            t.run()
        assert Path("output").exists()

        # `output` is now newer than its sources; `input2` no longer writes to
        # it, so the content changes while only `input1` remains as a source
        fs.reset()
        with filedb(fs=fs) as db:
            t = Transaction(db)
            t.write(Path("output"), "from one only", [Path("input1")])
            assert isinstance(t.actions[0], Write)
            # `output` was not touched outside of Entangled, so this is fine
            assert t.all_ok()
            t.run()

        assert "from one only" in Path("output").read_text()
