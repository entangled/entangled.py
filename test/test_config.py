from typing import Any

import msgspec
from entangled.config.config_update import ConfigUpdate
from entangled.config.version import Version
from entangled.config.language import Language, Comment
from entangled.config import config, Config, AnnotationMethod
from entangled.commands import tangle

from contextlib import chdir
from time import sleep
from pathlib import Path


def construct[T](cls: type[T], obj: object) -> T:
    return msgspec.convert(obj, type=cls)


def test_config_constructable():
    assert construct(
        Language,
        {"name": "French", "identifiers": ["fr"], "comment": {"open": "excusez moi"}},
    ) == Language("French", ["fr"], Comment("excusez moi"))
    cfg1 = Config() | construct(ConfigUpdate, {"version": "2.0", "annotation": "naked"})
    assert cfg1.version == Version(numbers=(2, 0))
    assert cfg1.annotation == AnnotationMethod.NAKED


config_with_language = """
version = "2.0"
annotation = "naked"

[[languages]]
name = "Fish"
identifiers = ["fish"]
comment = { open = "#" }
"""

md_source = """
``` {.fish file=test.fish}
echo hello world
```
"""


def test_new_language(tmp_path):
    with chdir(tmp_path):
        Path("entangled.toml").write_text(config_with_language)
        Path("test.md").write_text(md_source)
        sleep(0.1)
        config.read(force=True)
        assert config.get.annotation == AnnotationMethod.NAKED
        tangle()
        sleep(0.1)
        assert Path("test.fish").exists()
        assert Path("test.fish").read_text() == "echo hello world\n"


config_with_more = """
# required: the minimum version of Entangled
version = "2.0"

# default watch_list is ["**/*.md"]
watch_list = ["docs/**/*.md"]

[[languages]]
name = "Custom Java"
identifiers = ["java"]
comment = { open = "//" }

[[languages]]
name = "XML"
identifiers = ["xml", "html", "svg"]
comment = { open = "<!--", close = "-->" }
"""


def test_more_language(tmp_path):
    with chdir(tmp_path):
        Path("entangled.toml").write_text(config_with_more)
        sleep(0.1)
        config.read(force=True)

        html = config.get_language("html")
        assert html is not None
        assert html.name == "XML"

        java = config.get_language("java")
        assert java is not None
        assert java.name == "Custom Java"


config_in_pyproject = """
[tool.entangled]
version = "2.0"
watch_list = ["docs/*.md"]
"""


def test_pyproject_toml(tmp_path):
    with chdir(tmp_path):
        Path("pyproject.toml").write_text("answer=42")
        sleep(0.1)
        config.read(force=True)

        assert config.get == Config()

        Path("pyproject.toml").write_text(config_in_pyproject)
        sleep(0.1)
        config.read(force=True)

        assert config.get.watch_list == ["docs/*.md"]
