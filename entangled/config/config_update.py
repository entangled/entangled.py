from msgspec import Struct, field

from .document_style import DocumentStyle
from .language import Language
from .markers import Markers, default_markers, basic_markers
from .annotation_method import AnnotationMethod
from .namespace_default import NamespaceDefault

from brei import Program


class ConfigUpdate(Struct):
    """An update to existing config. This actually sets the API for all
    config input.

    Attributes:
        version: updates to the maximum.
        style: fills in a preset if given.
        languages: additive list of languages, identical identifiers will
            overrule existing ones.
        markers: overrides.
        watch_list: overrides.
        ignore_list: overrides.
        annotation_format: overrides.
        annotation: overrides.
        use_line_directives: overrides.
        hooks: additive, prepend a `~` character to disable a hook).
        hook: merged with `|` operator (overrides one deep).
        brei: overrides (TODO: implement merge, requires updating Brei).
    """
    version: str
    style: DocumentStyle | None = None
    languages: list[Language] = field(default_factory=list)
    markers: Markers | None = None
    watch_list: list[str] | None = None
    ignore_list: list[str] | None = None
    annotation_format: str | None = None
    annotation: AnnotationMethod | None = None
    use_line_directives: bool | None = None

    namespace_default: NamespaceDefault | None = None
    namespace: str | None = None

    hooks: list[str] = field(default_factory=list)
    hook: dict[str, object] | None = None
    brei: Program | None = None


prefab_config: dict[DocumentStyle, ConfigUpdate] = {
    DocumentStyle.DEFAULT: ConfigUpdate(
        version = "2.0",
        markers = default_markers,
        hooks = ["shebang"]
    ),
    DocumentStyle.BASIC: ConfigUpdate(
        version = "2.4",
        markers = basic_markers,
        hooks = ["quarto_attributes", "spdx_license", "shebang", "repl", "brei"]
    )
}
