import logging
from importlib.metadata import entry_points

from .base import HookBase, PrerequisitesFailed
from . import build, task, quarto_attributes
from ..config import config
from ..construct import construct


discovered_hooks = entry_points(group="entangled.hooks")


external_hooks = {
    name: discovered_hooks[name].load().Hook
    for name in discovered_hooks.names
}

hooks: dict[str, type[HookBase]] = {
    "build": build.Hook,
    "brei": task.Hook,
    "quarto_attributes": quarto_attributes.Hook }


def get_hooks() -> list[HookBase]:
    active_hooks = []
    for h in config.hooks:
        if h in hooks | external_hooks:
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
