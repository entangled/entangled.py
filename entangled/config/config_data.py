from __future__ import annotations

from copy import copy
from dataclasses import dataclass, field
from .version import Version
from .language import Language, languages
from .markers import Markers, default_markers
from .annotation_method import AnnotationMethod
from .namespace_default import NamespaceDefault
from .config_update import ConfigUpdate, prefab_config

from brei import Program


@dataclass(frozen=True)
class Config:
    """Main config class.

    Attributes:
        version: Version of Entangled for which this config was created.
            Entangled should read all versions lower than its own.
        languages: Dict of programming languages and their comment styles.
        markers: Regexes for detecting open and close of code blocks.

        watch_list: List of glob-expressions indicating files to include
            for tangling.
        ignore_list: List of glob-expressions black-listing files, overrides
            anything in the watch_list.

        annotation: Style of annotation.
        annotation_format: Extra annotation.

        use_line_directives: Wether to print pragmas in source code for
            indicating markdown source locations.
        hooks: List of enabled hooks.
        hook: Sub-config of hooks.
    """
    version: Version = Version((2, 0))
    languages: dict[str, Language] = field(default_factory=lambda: {
        i: lang for lang in languages for i in lang.identifiers
    })
    markers: Markers = field(default_factory=lambda: default_markers)

    watch_list: list[str] = field(default_factory=lambda: ["**/*.md"])
    ignore_list: list[str] = field(default_factory=list)

    annotation_format: str | None = None
    annotation: AnnotationMethod = AnnotationMethod.STANDARD
    use_line_directives: bool = False

    namespace_default: NamespaceDefault = NamespaceDefault.GLOBAL
    namespace: tuple[str, ...] | None = None

    hooks: set[str] = field(default_factory=lambda: { "shebang" })
    hook: dict[str, object] = field(default_factory=dict)
    brei: Program = field(default_factory=Program)

    def get_language(self, lang_id: str) -> Language | None:
        return self.languages.get(lang_id, None)

    def __or__(self, update: ConfigUpdate | None) -> Config:
        if update is None:
            return self

        if update.style is not None:
            x = self | prefab_config[update.style]
        else:
            x = self

        version = max(x.version, Version.from_str(update.version))
        languages = copy(x.languages)
        for lang in update.languages:
            for id in lang.identifiers:
                languages[id] = lang

        markers = x.markers if update.markers is None else update.markers
        watch_list = x.watch_list if update.watch_list is None else update.watch_list
        ignore_list = x.ignore_list if update.ignore_list is None else update.ignore_list
        annotation_format = x.annotation_format if update.annotation_format is None \
            else update.annotation_format
        annotation = x.annotation if update.annotation is None else update.annotation
        use_line_directives = x.use_line_directives if update.use_line_directives is None \
            else update.use_line_directives

        namespace_default = x.namespace_default if update.namespace_default is None \
            else update.namespace_default
        namespace = x.namespace if update.namespace is None \
            else tuple(update.namespace.split("::"))

        hook = x.hook if update.hook is None else x.hook | update.hook
        brei = x.brei if update.brei is None else update.brei

        hooks = copy(x.hooks)
        for uh in update.hooks:
            if uh.startswith("~"):
                h = uh.removeprefix("~")
                if h in hooks:
                    hooks.remove(h)
            else:
                hooks.add(uh)

        return Config(
            version, languages, markers, watch_list, ignore_list,
            annotation_format, annotation, use_line_directives,
            namespace_default, namespace, hooks, hook, brei)
