from contextlib import chdir
from pathlib import Path

import pytest

from entangled.commands.sync import run_sync
from entangled.errors.user import StitchConflict
from entangled.io.stat import hexdigest

CONFIG = """
version = "2.4"
style = "basic"
""".lstrip()

# The block `shared` is tangled into two files, the second time indented.
SHARED_MD = """
```python
#| file: a.py
<<shared>>
```

```python
#| file: b.py
def wrapper():
    <<shared>>
```

```python
#| id: shared
x = 1

y = 2
```
""".lstrip()


@pytest.fixture
def project(tmp_path: Path):
    (tmp_path / "entangled.toml").write_text(CONFIG)
    (tmp_path / "doc.md").write_text(SHARED_MD)
    with chdir(tmp_path):
        run_sync()
        yield tmp_path


def edit(path: Path, old: str, new: str):
    path.write_text(path.read_text().replace(old, new))


def test_stitch_keeps_edit_to_shared_block(project: Path):
    """An edit to one target must not be undone by another, unchanged target
    that contains the same block. The edit is forwarded to the other target."""
    edit(project / "a.py", "x = 1", "x = 42")
    run_sync()
    assert "x = 42" in (project / "doc.md").read_text()
    assert "x = 42" in (project / "a.py").read_text()
    assert "x = 42" in (project / "b.py").read_text()


def test_stitch_conflicting_edits(project: Path):
    edit(project / "a.py", "x = 1", "x = 2")
    edit(project / "b.py", "x = 1", "x = 3")
    with pytest.raises(StitchConflict):
        run_sync()
    assert (project / "doc.md").read_text() == SHARED_MD


def test_stitch_same_edit_in_two_targets(project: Path):
    edit(project / "a.py", "x = 1", "x = 2")
    edit(project / "b.py", "x = 1", "x = 2")
    run_sync()
    assert "x = 2" in (project / "doc.md").read_text()


def test_tangle_indented_blank_lines(project: Path):
    """Blank lines in an indented reference get no trailing white space."""
    for line in (project / "b.py").read_text().splitlines():
        assert line == line.rstrip()


def test_tangle_blank_lines_with_white_space(tmp_path: Path):
    """White space on blank lines in the markdown doesn't end up in the code."""
    (tmp_path / "entangled.toml").write_text(CONFIG)
    (tmp_path / "doc.md").write_text(
        "```python\n#| file: c.py\nx = 1\n    \ny = 2\n```\n")
    with chdir(tmp_path):
        run_sync()
    assert (tmp_path / "c.py").read_text().splitlines()[2] == ""


# Code lines with trailing white space, and a blank line with white space.
# Written out line by line, so that a formatter can't strip it from this file.
TRAILING_MD = "".join(line + "\n" for line in [
    "```python",
    "#| file: d.py",
    "def f():  ",
    "    return 1\t",
    "    ",
    "x = f()  ",
    "```",
])


def strip_trailing(text: str) -> str:
    """What a formatter does: strip trailing white space on every line."""
    return "".join(line.rstrip() + "\n" for line in text.splitlines())


@pytest.fixture
def trailing(tmp_path: Path):
    (tmp_path / "entangled.toml").write_text(CONFIG)
    (tmp_path / "doc.md").write_text(TRAILING_MD)
    with chdir(tmp_path):
        run_sync()
        yield tmp_path


def test_formatter_on_code_is_ignored(trailing: Path):
    """Stripping trailing white space from a tangled file, as many editors do
    on save, is not a change: nothing is stitched, and the file isn't
    rewritten."""
    d = trailing / "d.py"
    assert d.read_text() != strip_trailing(d.read_text())
    d.write_text(strip_trailing(d.read_text()))
    run_sync()
    assert (trailing / "doc.md").read_text() == TRAILING_MD
    assert d.read_text() == strip_trailing(d.read_text())
    assert "def f():\n" in d.read_text()


def test_formatter_on_markdown_is_ignored(trailing: Path):
    """Stripping trailing white space from the markdown is not a change
    either: the tangled file isn't rewritten."""
    md = trailing / "doc.md"
    code = (trailing / "d.py").read_text()
    md.write_text(strip_trailing(md.read_text()))
    run_sync()
    assert (trailing / "d.py").read_text() == code
    assert md.read_text() == strip_trailing(TRAILING_MD)


def test_hexdigest_ignores_trailing_white_space():
    assert hexdigest("a  \n\nb\t\r\n") == hexdigest("a\n\nb\n")
    assert hexdigest("a\nb") != hexdigest("a\n b")
