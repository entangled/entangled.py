import logging
from typing import Any
from .base import HookBase, PrerequisitesFailed
from . import build
from ..config import config
from ..construct import construct


hooks: dict[str, type[HookBase]] = {"build": build.Hook}


def get_hooks() -> list[HookBase]:
    active_hooks = []
    for h in config.hooks:
        if h in hooks:
            try:
                hook_cfg = construct(hooks[h].Config, config.hook.get(h, {}))
                hook_instance = hooks[h](hook_cfg)
                hook_instance.check_prerequisites()
                active_hooks.append(hook_instance)
            except PrerequisitesFailed as e:
                logging.error("hook `%s`: %s", h, str(e))
        else:
            logging.error("no such hook available: `%s`", h)
    return active_hooks


__all__ = ["hooks", "PrerequisitesFailed"]
