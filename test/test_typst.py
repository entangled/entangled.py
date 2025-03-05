from contextlib import chdir
from subprocess import run
from pathlib import Path
from shutil import copytree
import sys


def test_typst(tmp_path: Path, data: Path):
    copytree(data / "typst", tmp_path / "typst")
    run([sys.executable, "-m", "entangled.main", "tangle"],
        cwd=tmp_path / "typst", check=True)
    assert (tmp_path / "typst" / "fib.py").exists()
