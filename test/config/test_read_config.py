from entangled.config import read_config, read_config_from_toml, Config
from entangled.config.version import Version
from entangled.errors.user import UserError

from pathlib import Path
from contextlib import chdir

import pytest
import logging


pyproject_toml = """
[tool.entangled]
version = "100"
style = "basic"
""".lstrip()


def test_pyproject_toml(tmpdir: Path, caplog):
    with chdir(tmpdir):
        assert read_config() is None

    filename = tmpdir / "pyproject.toml"
    filename.write_text(pyproject_toml, encoding="utf-8")

    config = Config() | read_config_from_toml(filename, "tool.entangled")
    assert config.version == Version((100,))

    with caplog.at_level(logging.DEBUG):
        _ = read_config_from_toml(filename, "tool.not-entangled")
        assert "tool.not-entangled" in caplog.text

    with pytest.raises(UserError):
        _ = read_config_from_toml(filename, None)

    assert read_config_from_toml(tmpdir / "entangled.toml") is None

    with chdir(tmpdir):
        cfg = Config() | read_config()
        assert cfg.version == Version((100,))


entangled_toml = """
version = "42"
annotation = "naked"

[[languages]]
name = "Kernel"
identifiers = ["kernel"]
comment = {"open" = ";"}
""".lstrip()


def test_entangled_toml(tmpdir: Path, caplog):
    with chdir(tmpdir):
        assert read_config() is None

    (tmpdir / "entangled.toml").write_text(entangled_toml, encoding="utf-8")

    with chdir(tmpdir):
        cfg = Config() | read_config()
        assert cfg.version == Version((42,))
        assert cfg.get_language("kernel").name == "Kernel"


entangled_toml_error = """
no_version_given = ""
""".lstrip()


def test_entangled_toml_error(tmpdir: Path, caplog):
    (tmpdir / "entangled.toml").write_text(entangled_toml_error, encoding="utf-8")
    with chdir(tmpdir):
        with pytest.raises(UserError):
            cfg = Config() | read_config()

