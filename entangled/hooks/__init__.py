import logging
from .base import HookBase
from .build import BuildHook, PrerequisitesFailed
from ..config import config


hooks: dict[str, type[HookBase]] = {
    "build": BuildHook
}


def get_hooks() -> list[HookBase]:
    active_hooks = []
    for h in config.hooks:
        if h in hooks:
            try:
                hooks[h].check_prerequisites()
                active_hooks.append(hooks[h]())
            except PrerequisitesFailed as e:
                logging.error("hook `%s`: %s", h, str(e))
        else:
            logging.error("no such hook available: `%s`", h)
    return active_hooks


__all__ = ["hooks", "PrerequisitesFailed"]
