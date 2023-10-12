from __future__ import annotations
from ..status import find_watch_dirs, list_input_files, list_dependent_files
from ..config import config
from pathlib import Path

try:
    from rich.console import Console, Group
    from rich.columns import Columns
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree

    def tree_from_files(files):
        tree = Tree(label=".")
        dirs = {Path("."): tree}
        for f in sorted(files):
            for p in reversed(f.parents):
                if p not in dirs:
                    dirs[p] = dirs[p.parent].add(p.name, style="repr.path")
            dirs[f.parent].add(f.name, style="repr.filename")
        return tree

    def files_panel(file_list: list[str], title: str) -> Panel:
        tree = tree_from_files(file_list)
        return Panel(tree, title=title, border_style="dark_cyan")

    def rich_status():
        cfg = config.config
        config_table = Table()
        config_table.add_column("name")
        config_table.add_column("value")
        config_table.add_row(
            "Watch list", ", ".join(f"'{pat}'" for pat in cfg.watch_list)
        )
        config_table.add_row("Hooks enabled", ", ".join(cfg.hooks))

        console = Console(color_system="auto")
        group = Group(
            Panel(config_table, title="config", border_style="dark_cyan"),
            Columns(
                [
                    files_panel([str(f) for f in list_input_files()], "input files"),
                    files_panel(
                        [str(f) for f in list_dependent_files()], "dependent files"
                    ),
                ]
            ),
        )

        console.print(group)

    WITH_RICH = True
except ImportError:
    WITH_RICH = False


def status():
    if WITH_RICH:
        rich_status()
    else:
        print(config)
        print("---")
        print("input files:", sorted(list_input_files()))
