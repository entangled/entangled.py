from pathlib import Path
import time
import os
import threading
import pytest

from entangled.config import config
from entangled.filedb import stat
from entangled.commands.watch import _watch
from entangled.main import configure

from contextlib import chdir


def wait_for_file(filename, timeout=5):
    start_time = time.time()

    while time.time() - start_time < timeout:
        if os.path.exists(filename):
            return True
        time.sleep(0.1)

    return False


def wait_for_stat_diff(md_stat, filename, timeout=5):
    start_time = time.time()

    while time.time() - start_time < timeout:
        md_stat2 = stat(Path(filename))
        if md_stat != md_stat2:
            return True
        time.sleep(0.1)

    return False


@pytest.mark.timeout(30)
def test_daemon(tmp_path: Path):
    config.read(force=True)
    with chdir(tmp_path):
        try:
            configure(debug=True)
            stop = threading.Event()
            start = threading.Event()
            t = threading.Thread(target=_watch, args=(stop, start))
            t.start()
            # Wait for watch to boot up
            start.wait()
            Path("main.md").write_text(
                "``` {.scheme file=hello.scm}\n" '(display "hello") (newline)\n' "```\n"
            )
            wait_for_file("main.md")
            md_stat1 = stat(Path("main.md"))
            wait_for_file("hello.scm")
            assert Path("hello.scm").exists()

            lines = Path("hello.scm").read_text().splitlines()
            goodbye = '(display "goodbye") (newline)'
            lines.insert(2, goodbye)
            Path("hello.scm").write_text("\n".join(lines))
            wait_for_stat_diff(md_stat1, "main.md")
            md_stat2 = stat(Path("main.md"))
            assert md_stat1 != md_stat2
            assert md_stat1 < md_stat2

            lines = Path("main.md").read_text().splitlines()
            print(lines)
            assert lines[2] == goodbye

            lines[0] = "``` {.scheme file=foo.scm}"
            Path("main.md").write_text("\n".join(lines))

            wait_for_file("foo.scm")
            assert not Path("hello.scm").exists()
            assert Path("foo.scm").exists()

        finally:
            stop.set()
            t.join()
            time.sleep(0.1)
