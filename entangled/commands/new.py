from typing import Optional

import argh  # type: ignore
import argparse

from pathlib import Path
from brei.cli import RichHelpFormatter
from rich.console import Console
from rich.table import Table

from ..errors.user import HelpfulUserError

description = """Create a new entangled project from a template.

You can choose either one of the official supported, built-in templates (see:
entangled new -l), or any other template that copier supports, see:
https://copier.readthedocs.io/en/stable/reference/vcs/#copier.vcs.get_repo"""


def print_available_templates() -> None:
    from ..config.templates import templates as AVAILABLE_TEMPLATES
    from ..config.templates import Template

    table: Table = Table(title="Official Templates")
    table.add_column("Handle")
    table.add_column("Name")
    table.add_column("URL")
    table.add_column("Prerequisites")
    table.add_column("Description")

    t: Template
    for t in AVAILABLE_TEMPLATES:
        table.add_row(t.handle, t.name, t.url, t.prerequisites, t.description)

    console: Console = Console()
    console.print(table)
    print("\nUsage: entangled new [handle] [project_path]\n")


def print_help() -> None:
    """Print help as if '-h' was used.

    For this we first have to create a parser and attach this `new` function
    to it. Then we have a parser object that we can `print_help()` from.
    """
    parser = argparse.ArgumentParser(formatter_class=RichHelpFormatter)
    argh.add_commands(parser, [new], func_kwargs={"formatter_class": RichHelpFormatter})
    argh.utils.get_subparsers(parser).choices["new"].print_help()


@argh.arg(
    "-a",
    "--answers-file",
    help="Update using this path (relative to [project_path]) to find the answers file for `copier`",
)
@argh.arg(
    "-d",
    "--data",
    help='"VARIABLE1=VALUE1;VARIABLE1=VALUE2" Make VARIABLEs available as VALUEs when rendering the template; make sure to use quotation marks for multiple variables/values',
)
@argh.arg(
    "-D",
    "--defaults",
    help="Use default answers to questions, which might be null if not specified; overwrites when combined with -d!",
)
@argh.arg(
    "-p",
    "--pretend",
    help="Run but do not make any changes",
)
@argh.arg(
    "-o",
    "--overwrite",
    help="Overwrite files that already exist, without asking.",
)
@argh.arg(
    "-l",
    "--list-templates",
    help="List all official templates and exit",
)
@argh.arg(
    "-t",
    "--trust",
    help='Allow templates with unsafe features (Jinja extensions, migrations, tasks); "True" for officially supported templates',
)
@argh.arg(
    "template",
    # default=None,
    nargs="?",
    help="Template handle or URL; initialize a new project from this template",
)
@argh.arg(
    "project-path",
    # default=None,
    nargs="?",
    help="Initialize a new project at this path",
)
def new(
    template: Optional[str],
    project_path: Optional[Path], *,
    answers_file: Optional[str] = None,
    data: str = "",
    defaults: bool = False,
    pretend: bool = False,
    overwrite: bool = False,
    list_templates: bool = False,
    trust: bool = False,
) -> None:
    """Create a new entangled project from a template."""

    from ..config.templates import templates as AVAILABLE_TEMPLATES
    from ..config.templates import Template

    from copier import run_copy  # type: ignore
    from copier.errors import UnsafeTemplateError  # type: ignore

    if list_templates:
        print_available_templates()
        return

    if not template or not project_path:
        raise HelpfulUserError(
            "Please supply both a [template] and a [project_path].\n", print_help
        )

    copy_this_template: str = template
    trust_this_template: bool = trust

    # Use an officially supported template, if available, and trust it
    # If no template is found, treat the "template" var as URL or path for copier
    template_option: Template
    for template_option in AVAILABLE_TEMPLATES:
        if template == template_option.handle:
            trust_this_template = True
            copy_this_template = template_option.url
            break

    data_dict: dict = {}
    if data:
        try:
            for d in data.split(";"):
                if d:  # Allow for leading or trailing ";"
                    key, value = d.split("=")
                    data_dict[key] = value
        except ValueError:
            raise HelpfulUserError(
                "Invalid syntax for `-d/--data`. Please make sure "
                "to closely follow the example below.\n",
                print_help,
            )

    try:
        run_copy(
            src_path=copy_this_template,
            dst_path=project_path,
            answers_file=answers_file,
            data=data_dict,
            defaults=defaults,
            pretend=pretend,
            overwrite=overwrite,
            unsafe=trust_this_template,
        )
    # Suggest users to use --trust if needed
    except UnsafeTemplateError:
        raise HelpfulUserError(
            "Template uses potentially unsafe features. If you trust this template, "
            "consider adding the `--trust` option when running `entangled new`."
        )
    # If the [project_path] does not exist, `copier` catches a FileNotFoundError
    # and tries to create it. When this fails due to a PermissionError, the
    # FileNotFoundError is re-raised, but it's not the reason the operation
    # failed. We have to check for the reason for the FileNotFoundError to see
    # where it went wrong.
    except FileNotFoundError as e:
        if e.__context__.__class__ == PermissionError:
            raise HelpfulUserError(
                "A folder in [project_path] is not writable, please "
                "review its permissions."
            )
        else:
            raise HelpfulUserError(e.__str__())
    except PermissionError:
        raise HelpfulUserError(
            "A folder in [project_path] is not writable, please "
            "review its permissions."
        )
    # Display generic copier errors without stacktrace
    except Exception as e:
        if "Local template must be a directory" in e.__str__():
            raise HelpfulUserError(
                f'Template "{template}" not found. Please supply a valid path or '
                "URL,\nor use one of the officially supported ones from the "
                "following list:\n",
                print_available_templates,
            )
        elif "Question " in e.__str__():
            raise HelpfulUserError(
                "Template data missing.\nPlease supply a valid answers file "
                "with a path `relative` to the [project_path], or valid data "
                "with -d/--data.\n",
                print_help,
            )
        else:
            raise HelpfulUserError(
                f"The library `copier` gave an error:\n\n{e.__str__()}.\n\nIf you "
                "are trying to develop a template, please use `copier` directly, "
                "see https://copier.readthedocs.io .",
            )
