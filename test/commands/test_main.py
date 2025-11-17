from entangled.commands import main
from entangled.version import __version__

import pytest
import sys
import logging

from contextlib import chdir


def test_version(capsys):
    with pytest.raises(SystemExit):
        main(args=["--version"])
    captured = capsys.readouterr()
    assert captured.out.strip() == f"Entangled {__version__}"


def test_debug(caplog, tmpdir):
    caplog.set_level(logging.DEBUG)
    with chdir(tmpdir):
        with pytest.raises(SystemExit):
            main(args=["-d", "tangle"])

        assert "Welcome to Entangled" in caplog.text

