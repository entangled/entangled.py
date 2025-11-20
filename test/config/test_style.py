from entangled.config import Config, ConfigUpdate
from entangled.config.document_style import DocumentStyle
from entangled.config.markers import basic_markers


def test_style():
    cfg = Config()
    cfg1 = cfg | ConfigUpdate(version="2.4", style=DocumentStyle.BASIC)
    assert cfg1.markers is basic_markers
    assert "quarto_attributes" in cfg1.hooks

