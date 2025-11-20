from dataclasses import dataclass, field
from pathlib import PurePath, Path

from ..config import Config, ConfigUpdate, get_input_files, read_config, AnnotationMethod
from ..model import ReferenceMap, tangle_ref, Content, content_to_text
from ..io import Transaction
from ..readers import code
from ..iterators import numbered_lines, run_generator

from .context import Context, markdown
import logging


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
        self.config |= read_config()

    def input_files(self):
        return get_input_files(self.config)

    def source_text(self, path: Path) -> tuple[str, set[PurePath]]:
        deps = set()
        text = ""
        for content in self.content[path]:
            t, d = content_to_text(self.reference_map, content)
            if d is not None:
                deps.add(d)
            text += t
        return text, deps

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
        logging.debug("got config update: %s", update)
        self.content[path] = content
        t.update(path)
        return update

    def load_code(self, t: Transaction, path: Path):
        reader = code(numbered_lines(path, t.read(path)))
        for block in reader:
            self.reference_map[block.reference_id].source = block.content
        t.update(path)

    def load_all_code(self, t: Transaction):
        for tgt in self.reference_map.targets():
            if Path(tgt) in t.fs:
                self.load_code(t, Path(tgt))

    def load(self, t: Transaction):
        for p in get_input_files(self.config):
            self.load_source(t, p)

    def tangle(self, t: Transaction, annotation: AnnotationMethod | None = None):
        if annotation is None:
            annotation = self.config.annotation

        for h in self.context.hooks:
            h.pre_tangle(self.reference_map)

        for tgt in self.reference_map.targets():
            self.write_target(t, Path(tgt), annotation)

        for h in self.context.hooks:
            h.on_tangle(t, self.reference_map)

    def stitch(self, t: Transaction):
        for path in self.content:
            text, deps = self.source_text(path)
            t.write(path, text, map(Path, deps))

