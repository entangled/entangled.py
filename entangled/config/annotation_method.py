from enum import StrEnum


class AnnotationMethod(StrEnum):
    """Annotation methods.

    - `STANDARD` is the default. Comments tell where a piece of code
       came from in enough detail to reconstruct the markdown if some
       of the code is changed.
    - `NAKED` adds no comments to the tangled files. Stitching is not
       possible with this setting.
    - `SUPPLEMENTED` adds extra information to the comment lines.
    """

    STANDARD = "standard"
    NAKED = "naked"
    SUPPLEMENTED = "supplemented"
