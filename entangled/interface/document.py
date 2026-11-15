from dataclasses import dataclass, field
from pathlib import PurePath, Path

from ..config import Config, ConfigUpdate, get_input_files, read_config, AnnotationMethod
from ..model import ReferenceMap, ReferenceId, tangle_ref, Content, content_to_text
from ..io import AbstractFileCache, FileCache, Transaction
from ..readers import code
from ..iterators import numbered_lines, run_generator
from ..logging import logger
from ..errors.user import StitchConflict

from .context import Context, markdown


log = logger()


@dataclass
class Document:
    context: Context = field(default_factory=Context)
    reference_map: ReferenceMap = field(default_factory=ReferenceMap)
    content: dict[Path, list[Content]] = field(default_factory=dict)

    @property
    def config(self):
        return self.context.config

    @config.setter
    def config(self, new_config: Config) -> None:
        self.context.config = new_config

    def __post_init__(self):
        self.config |= read_config(self.context.fs)

    def input_files(self):
        return get_input_files(self.context.fs, self.config)

    def source_text(self, path: Path) -> tuple[str, set[PurePath]]:
        deps: set[PurePath] = set()
        # Use list for O(n) instead of O(n²) string concatenation
        text_parts: list[str] = []
        for content in self.content[path]:
            t, d = content_to_text(self.reference_map, content)
            if d is not None:
                deps.add(d)
            text_parts.append(t)
        return "".join(text_parts), deps

    def target_text(self, path: PurePath) -> tuple[str, set[PurePath]]:
        ref_name = self.reference_map.select_by_target(path)
        return tangle_ref(self.reference_map, ref_name, self.config.annotation)

    def write_target(self, t: Transaction, path: Path, annotation: AnnotationMethod | None = None):
        ref_name = self.reference_map.select_by_target(path)
        refs = self.reference_map.select_by_name(ref_name)
        main_block = self.reference_map[refs[0]]
        annotation = self.config.annotation if annotation is None else annotation
        text, deps = tangle_ref(self.reference_map, ref_name, annotation)
        t.write(path, text, map(Path, deps), main_block.mode)

    def load_source(self, t: Transaction, path: Path) -> ConfigUpdate | None:
        reader = markdown(self.context, self.reference_map, numbered_lines(path, t.read(path)))
        content, update = run_generator(reader)
        log.debug("got config update: %s", update)
        self.content[path] = content
        t.update(path)
        return update

    def load_code(self, t: Transaction, path: Path,
                  loaded: dict[ReferenceId, Path] | None = None):
        """Read code blocks back from a tangled file. If `loaded` is given, it
        records which file each block was read from, so that a block that
        was read before with different content raises a `StitchConflict`."""
        reader = code(numbered_lines(path, t.read(path)))
        for block in reader:
            ref = block.reference_id
            if loaded is not None:
                if ref in loaded and self.reference_map[ref].source != block.content:
                    raise StitchConflict(str(ref), (loaded[ref], path))
                loaded[ref] = path
            self.reference_map[ref].source = block.content
        t.update(path)

    def load_all_code(self, t: Transaction):
        """Read code blocks back from all targets that changed since they were
        tangled. Unchanged targets are skipped: they match the documentation,
        and when they share a block with a changed target, reading them would
        undo the change."""
        log.debug(f"Targets: {self.reference_map.targets()}")
        loaded: dict[ReferenceId, Path] = {}
        for tgt in self.reference_map.targets():
            path = Path(tgt)
            if path not in t.fs:
                continue
            if path in t.db and t.fs[path].stat == t.db[path]:
                log.debug(f"Skipping unchanged code: `{tgt}`")
                continue
            log.debug(f"Reading code: `{tgt}`")
            self.load_code(t, path, loaded)

    def load(self, t: Transaction):
        files = get_input_files(t.fs, self.config)
        if len(files) == 1:
            log.debug(f"single input file `{files[0]}`")
            self.context |= self.load_source(t, files[0])
        else:
            log.debug("multiple input files")
            for p in files:
                self.load_source(t, p)

    def tangle(self, t: Transaction, annotation: AnnotationMethod | None = None):
        if annotation is None:
            annotation = self.config.annotation

        for h in self.context.all_hooks:
            h.pre_tangle(self.reference_map)

        for tgt in self.reference_map.targets():
            self.write_target(t, Path(tgt), annotation)

        for h in self.context.all_hooks:
            h.on_tangle(t, self.reference_map)

    def stitch(self, t: Transaction):
        for path in self.content:
            text, deps = self.source_text(path)
            t.write(path, text, map(Path, deps))
