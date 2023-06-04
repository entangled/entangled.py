from entangled.config.version import Version
from entangled.config.language import Language, Comment
from entangled.config import config, Config, AnnotationMethod
from entangled.commands import tangle
from entangled.construct import construct
from entangled.utility import pushd

from time import sleep
from pathlib import Path

def test_config_constructable():
    assert construct(Version, "1.2.3") == Version((1, 2, 3))
    assert construct(
        Language,
        {"name": "French", "identifiers": ["fr"], "comment": {"open": "excusez moi"}},
    ) == Language("French", ["fr"], Comment("excusez moi"))
    assert construct(Config, {"version": "2.0"}) == Config(version=Version((2, 0)))
    assert construct(Config, {"version": "2.0", "annotation": "naked"}) == Config(
        version=Version((2, 0)), annotation=AnnotationMethod.NAKED
    )


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
    with pushd(tmp_path):
        Path("entangled.toml").write_text(config_with_language)
        Path("test.md").write_text(md_source)
        sleep(0.1)
        config.read()
        assert config.annotation == AnnotationMethod.NAKED
        tangle()
        sleep(0.1)
        assert Path("test.fish").exists()
        assert Path("test.fish").read_text() == "echo hello world"

