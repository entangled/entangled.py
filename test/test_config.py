from entangled.config.version import Version
from entangled.config.language import Language, Comment
from entangled.config import Config, AnnotationMethod
from entangled.construct import construct


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
