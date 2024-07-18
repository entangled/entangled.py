from contextlib import chdir
from subprocess import run
from pathlib import Path
from shutil import copytree

def test_typst(tmp_path: Path, data: Path):
    copytree(data / "typst", tmp_path / "typst")
    run(["python", "-m", "entangled.main", "tangle"],
        cwd=tmp_path / "typst", check=True)
    assert (tmp_path / "typst" / "fib.py").exists()
