import pytest
import unittest

from os.path import join
from typing import IO

from entangled.commands.new import new
from entangled.config.templates import Template, templates
from entangled.errors.user import HelpfulUserError


def test_print_available_templates() -> None:
    """Test if official template settings can be read"""
    new(template="", project_path="", list_templates=True)


def test_pretend_template_copy() -> None:
    """Test dry run"""
    new(
        template="./test/templates/minimal",
        project_path="_",
        data="project_name=my_project",
        defaults=True,
        pretend=True,
    )


def test_multiple_data() -> None:
    """Test `-d/--data` syntax"""
    new(
        template="./test/templates/minimal",
        project_path="_",
        data="project_name=my_project;key=value;",
        defaults=True,
        pretend=True,
    )


def test_minimal_template_copy(tmp_path) -> None:
    """Test if initializing a new project with a minimal template works"""
    new(
        template="./test/templates/minimal",
        project_path=str(tmp_path),
        data="project_name=my_project",
        defaults=True,
    )


def test_untrusted_template_pass(tmp_path) -> None:
    """Test if initializing a new project with an untrusted template fails"""
    new(
        template="./test/templates/minimal_unsafe",
        project_path=str(tmp_path),
        data="project_name=my_project",
        defaults=True,
        trust=True,
    )


def test_untrusted_template_fail(tmp_path) -> None:
    """Test if initializing a new project with an untrusted template fails"""
    with pytest.raises(HelpfulUserError, match="Template uses potentially unsafe"):
        new(
            template="./test/templates/minimal_unsafe",
            project_path=str(tmp_path),
            data="project_name=my_project",
            defaults=True,
        )


def test_overwrite_template(tmp_path) -> None:
    """Force overwrite a project with different data"""
    new(
        template="./test/templates/minimal",
        project_path=str(tmp_path),
        data="project_name=my_project",
        defaults=True,
    )
    new(
        template="./test/templates/minimal",
        project_path=str(tmp_path),
        data="project_name=my_other_project",
        defaults=True,
        overwrite=True,
    )


def test_default_answers_file(tmp_path) -> None:
    """Test pre-supplying answers to template questions"""
    default_answers_file: str = join(tmp_path, ".copier-answers.yml")
    f: IO
    with open(default_answers_file, "w") as f:
        f.write("project_name: default_project")
    new(
        template="./test/templates/minimal",
        project_path=str(tmp_path),
        defaults=True,
    )


def test_custom_answers_file(tmp_path) -> None:
    """Test pre-supplying answers to template questions"""
    my_answers_file_name = ".my-answers.yml"
    my_answers_file: str = join(tmp_path, my_answers_file_name)
    f: IO
    with open(my_answers_file, "w") as f:
        f.write("project_name: my_project")
    new(
        template="./test/templates/minimal",
        project_path=str(tmp_path),
        answers_file=my_answers_file_name,
        defaults=True,
    )
