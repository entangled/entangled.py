from pathlib import Path
import time
import os
import threading
import pytest
import sys

from entangled.io.stat import stat
from entangled.commands.watch import _watch
from entangled.logging import configure

from contextlib import chdir

if sys.platform.startswith("win"):
    pytest.skip("skipping test on windows until someone tells me how to fix this.", allow_module_level=True)


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


NO_CRASH_MAIN_MD1 = """
---
entangled:
    version: "2.4"
    style: "basic"
---

We have a missing reference here.

```python
#| file: test.py
<<test>>
```
""".lstrip()

NO_CRASH_MAIN_MD2 = """
---
entangled:
    version: "2.4"
    style: "basic"
---

Now it is fixed.

```python
#| file: test.py
<<test>>
```

```python
#| id: test
print("Hello, World")
```
""".lstrip()

@pytest.mark.timeout(10)
def test_no_crash(tmp_path: Path):
    """
    Test for issue #95; The watch process would crash on a UserError.
    With the new behaviour the process should not do anything, print
    a message, but keep running.
    """
    with chdir(tmp_path):
        configure(debug=True)
        stop = threading.Event()
        start = threading.Event()
        t = threading.Thread(target=_watch, args=(stop, start))
        try:
            t.start()
            # Wait for watch to boot up
            start.wait()

            Path("main.md").write_text(NO_CRASH_MAIN_MD1)
            time.sleep(0.1)
            assert not Path("test.py").exists()
            Path("main.md").write_text(NO_CRASH_MAIN_MD2)
            assert wait_for_file("test.py")

        finally:
            stop.set()
            t.join()
            time.sleep(0.1)


@pytest.mark.timeout(10)
def test_daemon(tmp_path: Path):
    with chdir(tmp_path):
        configure(debug=True)
        stop = threading.Event()
        start = threading.Event()
        t = threading.Thread(target=_watch, args=(stop, start))
        try:
            t.start()
            # Wait for watch to boot up
            start.wait()
            Path("main.md").write_text(
                "``` {.scheme file=hello.scm}\n" '(display "hello") (newline)\n' "```\n"
            )
            wait_for_file("main.md")
            md_stat1 = stat(Path("main.md"))
            assert md_stat1
            wait_for_file("hello.scm")
            assert Path("hello.scm").exists()

            lines = Path("hello.scm").read_text().splitlines()
            goodbye = '(display "goodbye") (newline)'
            lines.insert(2, goodbye)
            Path("hello.scm").write_text("\n".join(lines))
            assert wait_for_stat_diff(md_stat1, "main.md")
            md_stat2 = stat(Path("main.md"))
            assert md_stat2
            assert md_stat1.stat < md_stat2.stat

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
