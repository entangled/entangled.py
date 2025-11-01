from msgspec import Struct


class Markers(Struct, frozen=True):
    """Markers can be used to configure the Markdown dialect. Currently not used."""

    open: str
    close: str
    begin_ignore: str = r"^\s*\~\~\~markdown\s*$"
    end_ignore: str = r"^\s*\~\~\~\s*$"


default_markers = Markers(
    r"^(?P<indent>\s*)```\s*{(?P<properties>[^{}]*)}\s*$",
    r"^(?P<indent>\s*)```\s*$"
)

basic_markers = Markers(
    r"^(?P<indent>\s*)```(?P<properties>.*)$",
    r"^(?P<indent>\s*)```\s*$"
)
