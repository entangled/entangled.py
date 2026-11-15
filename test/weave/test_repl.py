from pathlib import Path
from contextlib import chdir
import os

import msgspec
import pytest
from repl_session import (
    JupyterConfig, ReplCommand, ReplConfig, ReplOutput, ReplSession, read_session, run_session,
    write_session
)

from entangled.commands import main
from entangled.hooks.repl import backend_config
from entangled.interface import Context
from entangled.weave import filters, transform_markdown


md_in = """# Session

``` {.python .repl #s session=s.json}
print("hi")
6 * 7
```

``` {.python #s}
x = 1
```

``` {.python .repl #s}
plot()
```

``` {.python .repl #s}
1/0
```
"""

jupyter = JupyterConfig(kernel="python3")


def write_output(*commands: ReplCommand):
    session = ReplSession(config=jupyter, commands=list(commands))
    _ = Path("s.out.json").write_bytes(msgspec.json.encode(session))


def session_commands() -> list[ReplCommand]:
    return [
        ReplCommand('print("hi")\n6 * 7', outputs=[
            ReplOutput("stdout", {"text/plain": "hi\n"}),
            ReplOutput("result", {"text/plain": "42"})]),
        ReplCommand("x = 1", outputs=[]),
        ReplCommand("plot()", outputs=[
            ReplOutput("display", {"text/plain": "<Figure>", "image/png": "iVBO\nRw0K"}),
            ReplOutput("display", {"text/plain": "<HTML>", "text/html": "<b>bold</b>"})]),
        ReplCommand("1/0", outputs=[
            ReplOutput("error", {"text/plain": "ZeroDivisionError: ```"})]),
    ]


def weave(text: str) -> str:
    return "".join(transform_markdown(Context(), text, filters["repl"]))


def test_repl_outputs(tmp_path: Path):
    with chdir(tmp_path):
        write_output(*session_commands())
        out = weave(md_in)

    assert '6 * 7\n```\n\n``` {.text .output .stdout}\nhi\n```\n\n``` {.text .output}\n42\n```\n' in out
    assert "x = 1\n```\n\n``` {.python .repl #s}" in out
    assert "\n![](data:image/png;base64,iVBORw0K)\n" in out
    assert "\n<b>bold</b>\n" in out
    assert "<Figure>" not in out
    assert "\n```` {.text .output .error}\nZeroDivisionError: ```\n````\n" in out


def test_repl_mime_type_and_legacy_output(tmp_path: Path):
    text = "``` {.python .repl #s session=s.json mime-type=text/plain}\n6 * 7\n```"
    with chdir(tmp_path):
        write_output(ReplCommand("6 * 7", output="42"))
        assert weave(text) == text + "\n\n``` {.text .output}\n42\n```\n"

        text = text.replace("text/plain", "text/html")
        write_output(ReplCommand("6 * 7", output_type="text/html", outputs=[
            ReplOutput("result", {"text/plain": "42", "text/html": "<i>42</i>"})]))
        assert weave(text) == text + "\n\n<i>42</i>\n"


def test_repl_rewritten_with_same_mtime(tmp_path: Path):
    text = "``` {.python .repl #s session=s.json}\n6 * 7\n```"
    with chdir(tmp_path):
        write_output(ReplCommand("6 * 7", output="42"))
        stat = Path("s.out.json").stat()
        assert "\n42\n" in weave(text)

        # File systems with coarse timestamps can give a rewritten file the same mtime.
        write_output(ReplCommand("6 * 7", output="forty-two"))
        os.utime("s.out.json", ns=(stat.st_atime_ns, stat.st_mtime_ns))
        assert "\nforty-two\n" in weave(text)


def test_repl_missing_or_stale(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    with chdir(tmp_path):
        assert weave(md_in) == md_in
        assert "not found" in caplog.text

        commands = session_commands()
        commands[2].command = "plot(1)"
        write_output(*commands[:3])
        out = weave(md_in)

    assert "out of date" in caplog.text
    assert "no output for this code block" in caplog.text
    assert "``` {.text .output}\n42\n```" in out
    assert "image/png" not in out


def test_backend_config():
    cfg = {"command": "python -q", "first_prompt": ">>> ", "change_prompt": "", "prompt": ""}
    assert isinstance(backend_config(cfg), ReplConfig)
    assert backend_config({"backend": "jupyter", "kernel": "python3"}) == jupyter


jupyter_toml = """
version = "2.0"
watch_list = ["doc.md"]
hooks = ["repl"]

[hook.repl.config.Python]
backend = "jupyter"
kernel = "python3"
"""

jupyter_md = """# Jupyter

``` {.python .repl #k session=k.json}
print("hi")
6 * 7
```

``` {.python .repl #k}
from IPython.display import HTML
HTML("<b>bold</b>")
```
"""


@pytest.mark.timeout(120)
def test_jupyter_session(tmp_path: Path):
    _ = pytest.importorskip("ipykernel")
    _ = pytest.importorskip("jupyter_client")

    with chdir(tmp_path):
        _ = Path("entangled.toml").write_text(jupyter_toml)
        _ = Path("doc.md").write_text(jupyter_md)
        main(args=["tangle"], standalone_mode=False)

        with Path("k.json").open() as f:
            session = read_session(f)
        assert session.config == jupyter
        with Path("k.out.json").open("w") as f:
            write_session(run_session(session), f)

        main(args=["weave", "-f", "repl", "-o", "out.md", "doc.md"], standalone_mode=False)
        out = Path("out.md").read_text()

    assert "``` {.text .output .stdout}\nhi\n```" in out
    assert "``` {.text .output}\n42\n```" in out
    assert "\n<b>bold</b>\n" in out
