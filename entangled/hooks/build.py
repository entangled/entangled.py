from tempfile import TemporaryDirectory
from pathlib import Path
from subprocess import run, SubprocessError, DEVNULL

import logging

from ..properties import Property, get_id, get_attribute
from ..tangle import tangle_ref
from ..document import ReferenceMap, CodeBlock

from .base import HookBase, PrerequisitesFailed

preamble = """
.RECIPEPREFIX = >
.PHONY = all

all: {targets}

{rules}
"""


class BuildHook(HookBase):
    def __init__(self):
        self.targets = []

    @staticmethod
    def check_prerequisites():
        try:
            run(["make", "--version"], stdout=DEVNULL)
        except (SubprocessError, FileNotFoundError):
            raise PrerequisitesFailed("GNU Make needs to be installed")

    def condition(self, props: list[Property]):
        return get_id(props) == "build" and \
            get_attribute(props, "target") is not None
    
    def on_read(self, _, code: CodeBlock):
        target = get_attribute(code.properties, "target")
        if target is None:
            return
        self.targets.append(target)
    
    def post_tangle(self, refs: ReferenceMap):
        logging.info("Building artifacts with `make`.")
        with TemporaryDirectory() as _pwd:
            pwd = Path(_pwd)
            script = preamble.format(
                targets=" ".join(self.targets),
                rules=tangle_ref(refs, "build")[0])
            (pwd / "Makefile").write_text(script)
            run(["make", "-f", str(pwd / "Makefile")], stdout=DEVNULL)