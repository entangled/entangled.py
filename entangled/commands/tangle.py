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
            doc.tangle(t, annotate)
            t.clear_orphans()

        for h in doc.context.all_hooks:
            h.post_tangle(doc.reference_map)

    except UserError as e:
        e.handle()
