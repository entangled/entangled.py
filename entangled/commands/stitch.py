import click

from ..interface import Document
from ..io import transaction, TransactionMode
from ..errors.user import UserError


@click.command()
@click.option("-f", "--force", help="force overwrite on conflict")
@click.option("-s", "--show", help="only show, don't act")
def stitch(*, force: bool = False, show: bool = False):
    """Stitch code changes back into the Markdown"""
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
            doc.load_all_code(t)
            doc.stitch(t)

    except UserError as e:
        e.handle()
