from dataclasses import dataclass, field
from pathlib import PurePath, Path

from ..config import Config, get_input_files, read_config, AnnotationMethod
from ..model import ReferenceMap, tangle_ref, Content, content_to_text
from ..io import Transaction
from ..readers import markdown, code
from ..iterators import numbered_lines, run_generator


@dataclass
class Document:
    config: Config = Config()
    reference_map: ReferenceMap = field(default_factory=ReferenceMap)
    content: dict[Path, list[Content]] = field(default_factory=dict)

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

    def load_source(self, t: Transaction, path: Path):
        reader = markdown(self.config, self.reference_map, numbered_lines(path, t.read(path)))
        t.update(path)
        content, _ = run_generator(reader)
        self.content[path] = content
        t.update(path)

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
        for tgt in self.reference_map.targets():
            self.write_target(t, Path(tgt), annotation)

    def stitch(self, t: Transaction):
        for path in self.content:
            text, deps = self.source_text(path)
            t.write(path, text, map(Path, deps))

