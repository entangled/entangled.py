from subprocess import run
import sys
from repl_session import read_session

from pathlib import Path
from shutil import copytree
from contextlib import chdir

def test_tangle_ref(data, tmp_path):
    copytree(data / "repl-hook", tmp_path / "repl-hook")
    with chdir(tmp_path / "repl-hook"):
        run([sys.executable, "-m", "entangled.main", "-d", "tangle"])
        assert Path("expected.yml").exists()
        assert Path("test.json").exists()

        expected = read_session(Path("expected.yml").open("r"))
        gotten = read_session(Path("test.json").open("r"))
        assert expected == gotten


def test_session_with_multiple_files(tmp_path):
    """Hooks configured in `entangled.toml` should also run `on_tangle` when
    there is more than one Markdown file."""
    with chdir(tmp_path):
        Path("entangled.toml").write_text(
            'version = "2.0"\nhooks = ["repl"]\n'
            "[hook.repl.config.Python]\n"
            'command = "python -q"\nfirst_prompt = ">>> "\n'
            'change_prompt = ""\nprompt = ""\n')
        Path("a.md").write_text("# A\n")
        Path("b.md").write_text(
            "``` {.python .repl #s session=s.json}\n6 * 7\n```\n")
        run([sys.executable, "-m", "entangled.main", "tangle"], check=True)
        session = read_session(Path("s.json").open("r"))
        assert [c.command for c in session.commands] == ["6 * 7"]
