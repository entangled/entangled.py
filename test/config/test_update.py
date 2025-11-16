from entangled.config import Config, ConfigUpdate


def test_null():
    cfg = Config()
    assert cfg | None is cfg

