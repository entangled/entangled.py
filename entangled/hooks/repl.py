import json
from typing import final, override

import msgspec

from entangled.config.language import Language
from .base import HookBase
from repl_session import ReplConfig, ReplSession, ReplCommand
from msgspec import Struct, field
from pathlib import Path

from ..logging import logger
from ..io import Transaction
from ..document import CodeBlock, ReferenceMap
from ..properties import Class, get_attribute, get_id


log = logger()

class Session(Struct):
    filename: Path
    language: str
    commands: list[ReplCommand]


def strip_comments(code: str, language: Language) -> str:
    def is_comment(line: str) -> bool:
        return line.startswith(language.comment.open)

    lines = code.splitlines()
    return "\n".join(l for l in lines if not is_comment(l))


@final
class Hook(HookBase):
    class Config(HookBase.Config):
        config: dict[str, ReplConfig] = field(default_factory=dict)

    def __init__(self, config: Config):
        super().__init__(config)
        self.config = config.config
        self.sessions: dict[str, Session] = {}

    @override
    def on_read(self, code: CodeBlock):
        """Called when the Markdown is being read, before the assembling of
        the reference map."""
        session_name = get_id(code.properties)
        if Class("repl") not in code.properties and session_name not in self.sessions.keys():
            return

        if code.language is None:
            log.error(f"{code.origin}: REPL hook triggered on codeblock without known language.")
            return

        lang_name = code.language.name
        if lang_name not in self.config.keys():
            log.error(f"{code.origin}: REPL hook triggered with unconfigured language `{lang_name}`.")
            return

        if session_name is None:
            log.error(f"{code.origin}: REPL hook triggered on code block without identifier.")
            return

        if session_name not in self.sessions.keys():
            filename = get_attribute(code.properties, "session")
            if filename is None:
                log.error(f"{code.origin}: REPL hook session opened without session attribute.")
                return

            self.sessions[session_name] = Session(Path(filename), lang_name, [])

        mime_type = get_attribute(code.properties, "mime-type") or "text/plain"
        self.sessions[session_name].commands.append(ReplCommand(
            strip_comments(code.source, code.language), output_type=mime_type))

    @override
    def on_tangle(self, t: Transaction, refs: ReferenceMap):
        """Executed after other targets were tangled, but during the same
        transaction. If you want to write a file, consider doing so as part of
        the transaction."""
        for s in self.sessions.values():
            rs_json = msgspec.json.encode(ReplSession(
                config = self.config[s.language],
                commands = s.commands))
            t.write(s.filename, rs_json.decode(), [])
