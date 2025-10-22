from entangled.markdown_reader import read_markdown_string
from entangled.tangle import tangle_ref
from entangled.code_reader import CodeReader

from pathlib import Path, PurePath
import os
from shutil import copytree, move
from contextlib import chdir


def test_tangle_ref(data, tmp_path):
    copytree(data / "os_interop", tmp_path / "os_interop")
    with chdir(tmp_path / "os_interop"):
        refs, _ = read_markdown_string(Path("doc/index.md").read_text(encoding="utf-8"), Path("doc/index.md"))
        tangled, deps = tangle_ref(refs, "src/euler_number.c")
        assert deps == {PurePath("doc/index.md")}
        with open("src/euler_number.c", "r") as f:
            assert f.read().strip() == tangled.strip()

        cb_old = next(refs["series-expansion"]).source
        cr = CodeReader("-", refs).run(Path("src/euler_number.c.edit").read_text())
        cb_new = next(refs["series-expansion"]).source
        assert cb_old != cb_new
