from pathlib import Path, PurePath
import sys

import rich_click as click

from .main import main

from ..config import read_config
from ..interface import Context
from ..weave import filters, filter_description, transform_markdown


def print_filters():
    width = max(map(len, filters))
    for name, f in filters.items():
        print(f"{name:<{width}}  {filter_description(f)}")


@main.command()
@click.argument("input", type=click.Path(dir_okay=False, allow_dash=True, path_type=Path),
                default="-")
@click.option("-o", "--output", type=click.Path(dir_okay=False, allow_dash=True, path_type=Path),
              default="-", help="output file, defaults to standard output")
@click.option("-f", "--filter", "filter_names", type=click.Choice(list(filters)), multiple=True,
              help="filter to apply, can be repeated; defaults to `label`")
@click.option("--list-filters", is_flag=True, help="list available filters and exit")
def weave(*, input: Path, output: Path, filter_names: tuple[str, ...] = (),
          list_filters: bool = False):
    """Transform Markdown for rendering by documentation tools."""
    if list_filters:
        print_filters()
        return

    context = Context()
    context |= read_config(context.fs)

    if input == Path("-"):
        text = sys.stdin.read()
        filename = PurePath("-")
    else:
        text = input.read_text()
        filename = input

    selected = [filters[n] for n in (filter_names or ("label",))]
    result = "".join(transform_markdown(context, text, *selected, filename=filename))

    if output == Path("-"):
        _ = sys.stdout.write(result)
    else:
        _ = output.write_text(result)
