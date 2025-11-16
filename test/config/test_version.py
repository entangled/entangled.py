from entangled.config.version import Version


def test_version_class():
    assert Version.from_str("1.2.3") == Version((1, 2, 3))
    assert Version((2, 4, 1)).to_str() == "2.4.1"
    assert Version.from_str("2.3") < Version.from_str("5.1")

