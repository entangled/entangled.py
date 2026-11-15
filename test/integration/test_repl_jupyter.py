"""
End-to-end test of a REPL session with the Jupyter backend: a stand-alone
Markdown file, configured through its YAML header, tangles a module and uses
it in a session. We run the session and weave the results into the Markdown.
"""

from contextlib import chdir
from pathlib import Path
from shutil import copy

import pytest
from repl_session import read_session, run_session, write_session

from entangled.commands import main


@pytest.mark.timeout(120)
def test_repl_jupyter(tmp_path: Path, data: Path):
    _ = pytest.importorskip("ipykernel")
    _ = pytest.importorskip("jupyter_client")

    # Only copy the input: `expected.md` would be read too, with no
    # `entangled.toml` to restrict the watch list.
    _ = copy(data / "repl-jupyter" / "primes.md", tmp_path)

    with chdir(tmp_path):
        main(args=["tangle"], standalone_mode=False)
        assert "def primes(n: int) -> list[int]:" in Path("primes.py").read_text()

        with Path("session.json").open() as f:
            session = read_session(f)
        with Path("session.out.json").open("w") as f:
            write_session(run_session(session), f)

        main(args=["weave", "-f", "repl", "-o", "woven.md", "primes.md"], standalone_mode=False)
        woven = Path("woven.md").read_text()

    assert woven == (data / "repl-jupyter" / "expected.md").read_text()
