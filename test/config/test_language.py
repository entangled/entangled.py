from entangled.config import Config, ConfigUpdate
from entangled.config.language import Language, Comment


def test_get_language():
    cfg = Config()

    lang1 = cfg.get_language("scheme")
    assert lang1 is not None and lang1.name == "Lisp"

    lang2 = cfg.get_language("brainfuck")
    assert lang2 is None

    # pick a language that we'll never support out of the box ;)
    cobol = Language("COBOL", ["cobol"], Comment("*>"))
    cfg1 = cfg | ConfigUpdate(
        version="2.4",
        languages=[cobol])
    assert len(cfg1.languages) == len(cfg.languages) + 1
    assert cfg.get_language("cobol") is None
    assert cfg1.get_language("cobol") is cobol

