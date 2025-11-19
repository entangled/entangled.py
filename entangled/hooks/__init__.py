import logging
from importlib.metadata import entry_points

from .base import HookBase, PrerequisitesFailed
from . import build, task, quarto_attributes, shebang, spdx_license, repl
from ..config import Config
from typing import TypeVar
import msgspec

AbstractHook = TypeVar("AbstractHook", bound=HookBase)

discovered_hooks = entry_points(group="entangled.hooks")


external_hooks = {
    name: discovered_hooks[name].load().Hook for name in discovered_hooks.names  # pyright: ignore[reportAny]
}

hooks: dict[str, type[HookBase]] = {
    "build": build.Hook,
    "brei": task.Hook,
    "repl": repl.Hook,
    "shebang": shebang.Hook,
    "spdx_license": spdx_license.Hook,
    "quarto_attributes": quarto_attributes.Hook,
}


singletons: dict[str, HookBase] = {}


def get_singleton(cfg: Config, h: str) -> HookBase:
    if h not in singletons:
        try:
            hook_cfg = msgspec.convert(cfg.hook.get(h, {}), type=hooks[h].Config)
            hook_instance = hooks[h](hook_cfg)
            hook_instance.check_prerequisites()
            singletons[h] = hook_instance
        except PrerequisitesFailed as e:
            logging.error("hook `%s`: %s", h, str(e))
        except msgspec.ValidationError as e:
            logging.error("hook `%s`: %s", h, str(e))

    return singletons[h]


def get_hooks(cfg: Config) -> list[HookBase]:
    active_hooks: list[HookBase] = []
    for h in sorted(cfg.hooks, key=lambda h: hooks[h].priority()):
        if h in hooks | external_hooks:
            active_hooks.append(get_singleton(cfg, h))
        else:
            logging.error("no such hook available: `%s`", h)

    return active_hooks


__all__ = ["hooks", "PrerequisitesFailed", "get_hooks", "HookBase"]
