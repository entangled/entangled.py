from entangled.interface import Document
from entangled.io import transaction
from entangled.model import ReferenceName, ReferenceId

from pathlib import Path, PurePath
from shutil import copytree
from contextlib import chdir


def test_tangle_ref(data, tmp_path):
    copytree(data / "os_interop", tmp_path / "os_interop")
    with chdir(tmp_path / "os_interop"):
        doc = Document()
        with transaction() as t:
            doc.load_source(t, Path("doc/index.md"))
            euler_text, deps = doc.target_text(Path("src/euler_number.c"))
            assert deps == {PurePath("doc/index.md")}
            with open("src/euler_number.c", "r") as f:
                assert f.read().strip() == euler_text.strip()

        ref = ReferenceId(ReferenceName((), "series-expansion"), PurePath("doc/index.md"), 0)
        cb_old = doc.reference_map[ref].source
        doc.load_code(t, Path("src/euler_number.c.edit"))
        cb_new = doc.reference_map[ref].source
        assert cb_old != cb_new
