from entangled.main import cli
from entangled.version import __version__

from contextlib import contextmanager, chdir
import sys
import pytest
from pathlib import Path
from time import sleep


@contextmanager
def argv(*args):
    old = sys.argv
    sys.argv = ["entangled"] + list(args)
    yield
    sys.argv = old


def test_version(capsys):
    with argv("--version"):
        with pytest.raises(SystemExit):
            cli()
        captured = capsys.readouterr()
        assert captured.out.strip() == f"Entangled {__version__}"


def test_watch(tmp_path):
    with chdir(tmp_path):
        Path("./entangled.toml").write_text("\n".join(['version="2.0"']))
        Path("./test.md").write_text(
            "\n".join(["``` {.python file=test.py}", 'print("hello")', "```"])
        )

        with argv("--debug", "tangle"):
            cli()
            assert Path("./test.py").exists()
