from pathlib import Path
import time
import os
from entangled.config import config
from entangled.filedb import stat
import threading
from entangled.commands.watch import _watch
from entangled.main import configure

from contextlib import chdir

def test_daemon(tmp_path: Path):
    config.read()
    with chdir(tmp_path):
        try:
            configure(debug=True)
            stop = threading.Event()
            t = threading.Thread(target=_watch, args=(stop,))
            t.start()
            Path("main.md").write_text(
                "``` {.scheme file=hello.scm}\n" '(display "hello") (newline)\n' "```\n"
            )
            time.sleep(0.1)
            md_stat1 = stat(Path("main.md"))
            assert Path("hello.scm").exists()

            lines = Path("hello.scm").read_text().splitlines()
            goodbye = '(display "goodbye") (newline)'
            lines.insert(2, goodbye)
            Path("hello.scm").write_text("\n".join(lines))
            time.sleep(0.2)
            md_stat2 = stat(Path("main.md"))
            assert md_stat1 != md_stat2
            assert md_stat1 < md_stat2

            lines = Path("main.md").read_text().splitlines()
            print(lines)
            assert lines[2] == goodbye

            lines[0] = "``` {.scheme file=foo.scm}"
            Path("main.md").write_text("\n".join(lines))
            time.sleep(0.1)

            assert not Path("hello.scm").exists()
            assert Path("foo.scm").exists()

        finally:
            stop.set()
            t.join()
            time.sleep(0.1)
