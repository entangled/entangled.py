from entangled.io.stat import stat
from entangled.io.filedb import filedb
from time import sleep
from pathlib import Path
import pytest
from contextlib import chdir

from entangled.io.virtual import FileCache


@pytest.fixture(scope="session")
def example_files(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("test-filedb")
    with open(tmp_path / "a", "w") as f:
        f.write("hello")
    # modification times of b, c, and d need to be later than a
    sleep(0.01)
    with open(tmp_path / "b", "w") as f:
        f.write("hello")
    with open(tmp_path / "c", "w") as f:
        f.write("goodbye")
    with open(tmp_path / "d", "w") as f:
        f.write("earth")
    return tmp_path


def test_stat(example_files: Path):
    with chdir(example_files):
        stat_a = stat(example_files / "a")
        assert stat_a
        stat_b = stat(example_files / "b")
        assert stat_b
        stat_c = stat(example_files / "c")
        assert stat_c
        assert stat_a.stat == stat_b.stat
        assert stat_c.stat != stat_b.stat
        assert stat_a.stat < stat_b.stat


def test_filedb(example_files: Path):
    with chdir(example_files):
        fs = FileCache()
        with filedb() as db:
            for n in "abcd":
                db.update(fs, Path(n))

        fs.write(Path("d"), "mars")

        with filedb() as db:
            assert list(db.changed_files(fs)) == [Path("d")]
            db.update(fs, Path("d"))
            assert list(db.changed_files(fs)) == []
