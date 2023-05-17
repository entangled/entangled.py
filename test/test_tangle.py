from entangled.markdown_reader import read_markdown
from entangled.commands.tangle import tangle_ref
from entangled.utility import pushd
from pathlib import Path
import os


def test_tangle_ref(data):
    with pushd(data / "hello-world") as cwd:
        refs, _ = read_markdown(cwd / "hello-world.md")
        tangled, deps = tangle_ref(refs, "hello_world.cc")
        assert deps == {"hello-world.md"}
        with open("hello_world.cc", "r") as f:
            assert f.read() == tangled
