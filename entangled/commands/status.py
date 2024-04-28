from __future__ import annotations
from typing import Iterable
from ..status import find_watch_dirs, list_input_files, list_dependent_files
from ..config import config
from pathlib import Path

from rich.console import Console, Group
from rich.columns import Columns
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

def tree_from_files(files: Iterable[Path]):
    tree = Tree(label=".")
    dirs = {Path("."): tree}
    for f in sorted(files):
        for p in reversed(f.parents):
            if p not in dirs:
                dirs[p] = dirs[p.parent].add(p.name, style="repr.path")
        dirs[f.parent].add(f.name, style="repr.filename")
    return tree

def files_panel(file_list: Iterable[Path], title: str) -> Panel:
    tree = tree_from_files(file_list)
    return Panel(tree, title=title, border_style="dark_cyan")

def rich_status():
    config_table = Table()
    config_table.add_column("name")
    config_table.add_column("value")
    config_table.add_row(
        "Watch list", ", ".join(f"'{pat}'" for pat in config.watch_list)
    )
    config_table.add_row(
        "Ignore list", ", ".join(f"'{pat}'" for pat in config.ignore_list)
    )
    config_table.add_row("Hooks enabled", ", ".join(config.hooks))

    console = Console(color_system="auto")
    group = Group(
        Panel(config_table, title="config", border_style="dark_cyan"),
        Columns(
            [
                files_panel(list_input_files(), "input files"),
                files_panel(list_dependent_files(), "dependent files"),
            ]
        ),
    )

    console.print(group)


def status():
    config.read()
    rich_status()

