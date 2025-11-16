from entangled.config import Config, ConfigUpdate


def test_hooks_update():
    cfg = Config(hooks={"brei", "quarto_attributes"})
    cfg1 = cfg | ConfigUpdate(version="2.4", hooks=["~brei"])
    assert cfg1.hooks == {"quarto_attributes"}
    cfg2 = cfg | ConfigUpdate(version="2.4", hooks=["shebang"])
    assert cfg2.hooks == {"brei", "quarto_attributes", "shebang"}
