import logging
from importlib.metadata import entry_points

from .base import HookBase, PrerequisitesFailed
from . import build, task, quarto_attributes, shebang, spdx_license, repl
from ..config import config
from typing import TypeVar
import msgspec

AbstractHook = TypeVar("AbstractHook", bound=HookBase)

discovered_hooks = entry_points(group="entangled.hooks")


external_hooks = {
    name: discovered_hooks[name].load().Hook for name in discovered_hooks.names
}

hooks: dict[str, type[HookBase]] = {
    "build": build.Hook,
    "brei": task.Hook,
    "repl": repl.Hook,
    "shebang": shebang.Hook,
    "spdx_license": spdx_license.Hook,
    "quarto_attributes": quarto_attributes.Hook,
}


def get_hooks() -> list[HookBase]:
    active_hooks: list[HookBase] = []
    for h in config.get.hooks:
        if h in hooks | external_hooks:
            try:
                hook_cfg = msgspec.convert(config.get.hook.get(h, {}), type=hooks[h].Config)
                hook_instance = hooks[h](hook_cfg)
                hook_instance.check_prerequisites()
                active_hooks.append(hook_instance)
            except PrerequisitesFailed as e:
                logging.error("hook `%s`: %s", h, str(e))
            except msgspec.ValidationError as e:
                logging.error("hook `%s`: %s", h, str(e))
        else:
            logging.error("no such hook available: `%s`", h)

    return active_hooks


__all__ = ["hooks", "PrerequisitesFailed", "get_hooks"]
