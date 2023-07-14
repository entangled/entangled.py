from ..status import find_watch_dirs, list_input_files, list_dependent_files
from ..config import config
from pathlib import Path

try:
    from rich.console import Console, Group
    from rich.columns import Columns
    from rich.table import Table
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.tree import Tree

    WITH_RICH = True
except ImportError:
    WITH_RICH = False


def tree_from_files(files):
    tree = Tree(label=".")
    dirs = { Path("."): tree }
    for f in files:
        for p in f.parents[::-1]:
            if p not in dirs:
                dirs[p] = dirs[p.parent].add(str(p))
        dirs[f.parent].add(str(f))
    return tree


def rich_status():
    cfg = config.config
    config_table = Table()
    config_table.add_column("name")
    config_table.add_column("value")
    config_table.add_row("Watch list", ", ".join(f"'{pat}'" for pat in cfg.watch_list))
    config_table.add_row("Hooks enabled", ", ".join(cfg.hooks))

    console = Console(color_system="auto")
    group = Group(
        Panel(config_table, title="config", border_style="dark_cyan"),
        Columns((
            Panel(tree_from_files(list_input_files()), title="input files", border_style="dark_cyan"),
            Panel(tree_from_files(list_dependent_files()), title="dependent files", border_style="dark_cyan"))))

    console.print(group)


def status():
    if WITH_RICH:
        rich_status()
    else:
        print(config)
        print("---")
        print("input files:", sorted(list_input_files()))
