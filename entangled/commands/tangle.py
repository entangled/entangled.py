import click

from ..config import AnnotationMethod
from ..io import transaction, TransactionMode
from ..hooks import get_hooks
from ..errors.user import UserError
from ..interface import Document


@click.command
@click.option("-a", "--annotate", help="annotation method")
@click.option("-f", "--force", help="force overwriting existing files")
@click.option("-s", "--show", help="only show what would happen")
def tangle(*, annotate: AnnotationMethod | None = None, force: bool = False, show: bool = False):
    """Tangle codes from Markdown"""
    if show:
        mode = TransactionMode.SHOW
    elif force:
        mode = TransactionMode.FORCE
    else:
        mode = TransactionMode.FAIL

    try:
        doc = Document()

        with transaction(mode) as t:
            doc.load(t)
            hooks = get_hooks(doc.config)

            for h in hooks:
                h.pre_tangle(doc.reference_map)

            doc.tangle(t, annotate)

            for h in hooks:
                h.on_tangle(t, doc.reference_map)

            t.clear_orphans()

        for h in hooks:
            h.post_tangle(doc.reference_map)

    except UserError as e:
        e.handle()
