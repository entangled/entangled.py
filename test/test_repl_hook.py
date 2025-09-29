from subprocess import run
import sys
from repl_session import read_session

from pathlib import Path
from shutil import copytree
from contextlib import chdir

def test_tangle_ref(data, tmp_path):
    copytree(data / "repl-hook", tmp_path / "repl-hook")
    with chdir(tmp_path / "repl-hook"):
        run([sys.executable, "-m", "entangled.main", "tangle"])
        assert Path("expected.yml").exists()
        assert Path("test.json").exists()

        expected = read_session(Path("expected.yml").open("r"))
        gotten = read_session(Path("test.json").open("r"))
        assert expected == gotten
