from contextlib import chdir
from entangled.commands import tangle, stitch
from entangled.config import config
from entangled.filedb import stat
from entangled.errors.user import UserError

import pytest
from time import sleep
from pathlib import Path


def test_modes(tmp_path: Path):
    with chdir(tmp_path):
        (tmp_path / "entangled.toml").write_text(
            'version = "2.0"\n' 'watch_list = ["docs/**/*.md"]\n'
        )
        config.read()
        md = tmp_path / "docs" / "index.md"
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text("``` {.python file=src/hello.py}\n" 'print("hello")\n' "```\n")

        tangle()
        sleep(0.1)
        target = tmp_path / "src" / "hello.py"
        assert target.exists()
        hello_stat1 = stat(target)
        hello_src = target.read_text().splitlines()
        assert hello_src[1] == 'print("hello")'

        md.write_text("``` {.python file=src/hello.py}\n" 'print("goodbye")\n' "```\n")
        sleep(0.1)
        md_stat1 = stat(md)

        tangle(show=True)
        sleep(0.1)
        hello_stat2 = stat(target)
        assert hello_stat2 == hello_stat1
        assert not (hello_stat2 > hello_stat1)

        hello_src[1] = 'print("bonjour")'
        (tmp_path / "src" / "hello.py").write_text("\n".join(hello_src))
        sleep(0.1)
        hello_stat1 = stat(target)

        # with pytest.raises(UserError):
        tangle()
        sleep(0.1)
        hello_stat2 = stat(target)
        assert hello_stat2 == hello_stat1
        assert not (hello_stat2 > hello_stat1)

        # with pytest.raises(UserError):
        stitch()
        sleep(0.1)
        md_stat2 = stat(md)
        print(md.read_text())
        assert md_stat1 == md_stat2
        assert not (md_stat2 > md_stat1)

        stitch(force=True)
        sleep(0.1)
        md_stat2 = stat(md)
        assert md_stat1 != md_stat2
        assert md_stat2 > md_stat1
