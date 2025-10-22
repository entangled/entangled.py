from entangled.markdown_reader import read_markdown_string
from entangled.tangle import tangle_ref
from entangled.code_reader import CodeReader
from pathlib import Path, PurePath
import os
from shutil import copytree, move
from contextlib import chdir


def test_tangle_ref(data, tmp_path):
    copytree(data / "hello-world", tmp_path / "hello-world")
    with chdir(tmp_path / "hello-world"):
        refs, _ = read_markdown_string(Path("hello-world.md").read_text(encoding="utf-8"), Path("hello-world.md"))
        tangled, deps = tangle_ref(refs, "hello_world.cc")
        assert deps == {PurePath("hello-world.md")}
        with open("hello_world.cc", "r") as f:
            assert f.read() == tangled

        cb_old = next(refs["hello-world"]).source
        cr = CodeReader("-", refs).run(Path("hello_universe.cc").read_text())
        cb_new = next(refs["hello-world"]).source
        assert cb_old != cb_new
