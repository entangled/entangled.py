import rich_click as click

from .main import main

from ..config import AnnotationMethod
from ..io import transaction, TransactionMode
from ..errors.user import UserError
from ..interface import Document


@main.command()
@click.option("-a", "--annotate", type=click.Choice(AnnotationMethod, case_sensitive=False),
              help="annotation method")
@click.option("-f", "--force", is_flag=True, help="force overwriting existing files")
@click.option("-s", "--show", is_flag=True, help="only show what would happen")
def tangle(*, annotate: AnnotationMethod | None = None, force: bool = False, show: bool = False):
    """Tangle codes from the documentation."""
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

            for h in doc.context.hooks:
                h.pre_tangle(doc.reference_map)

            doc.tangle(t, annotate)

            for h in doc.context.hooks:
                h.on_tangle(t, doc.reference_map)

            t.clear_orphans()

        for h in doc.context.hooks:
            h.post_tangle(doc.reference_map)

    except UserError as e:
        e.handle()
