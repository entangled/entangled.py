"""
The `build` hook collects code blocks that are tagged with the `#build`
identifier and have a `target=` attribute defined.  These code blocks are put
together into a temporary Makefile that is run from the current working
directory.
"""

from tempfile import TemporaryDirectory
from pathlib import Path
from subprocess import run, SubprocessError, DEVNULL

import logging
import os

from ..properties import Property, get_id, get_attribute
from ..tangle import tangle_ref
from ..document import ReferenceMap, CodeBlock

from .base import HookBase, PrerequisitesFailed

"""
The Makefile is generated with `preamble` as a format string.  The
`.RECIPEPREFIX` is set to `>` , and `target` attributes are collected into an
`all` target.
"""
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
        """Check that `make` is installed."""
        try:
            run(["make", "--version"], stdout=DEVNULL)
        except (SubprocessError, FileNotFoundError):
            raise PrerequisitesFailed("GNU Make needs to be installed")

    def condition(self, props: list[Property]):
        """Condition by which a CodeBlock is processed: should have `#build` id
        and `target=` attribute."""
        return get_id(props) == "build" and get_attribute(props, "target") is not None

    def on_read(self, _, code: CodeBlock):
        """Add a CodeBlock's target attribute to the list of targets."""
        target = get_attribute(code.properties, "target")
        if target is None:
            return
        self.targets.append(target)

    def post_tangle(self, refs: ReferenceMap):
        """After all code is tangled: retrieve the `#build` script and run it."""
        if "CI" in os.environ:
            logging.info("CI run detected, skipping `build` hook.")
            return

        logging.info("Building artifacts with `make`.")
        with TemporaryDirectory() as _pwd:
            pwd = Path(_pwd)
            script = preamble.format(
                targets=" ".join(self.targets), rules=tangle_ref(refs, "build")[0]
            )
            (pwd / "Makefile").write_text(script)
            run(["make", "-f", str(pwd / "Makefile")], stdout=DEVNULL)
