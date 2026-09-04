"""Plugin registry for Kaihou Engine.

The registry reads ``config/plugins.yaml`` and dynamically imports the
listed plugin classes.  Each entry must point to a callable that returns a
plugin instance (most plugins expose a ``Plugin`` class at the module
level).
"""

from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List

import yaml

from ..core.exceptions import ConfigError, PluginError

# ---------------------------------------------------------------------------
# Helper to import a dotted path and return the attribute (class or factory)
# ---------------------------------------------------------------------------

def _import_attribute(dotted_path: str) -> Any:
    module_path, _, attr_name = dotted_path.rpartition(".")
    if not module_path:
        raise PluginError(f"Invalid plugin path: '{dotted_path}' (no module)")
    try:
        module = import_module(module_path)
    except ImportError as exc:
        raise PluginError(f"Failed to import plugin module '{module_path}': {exc}") from exc
    try:
        return getattr(module, attr_name)
    except AttributeError as exc:
        raise PluginError(f"Plugin module '{module_path}' has no attribute '{attr_name}'") from exc


def load_plugins() -> Dict[str, Any]:
    """Load all plugins defined in ``config/plugins.yaml``.

    Returns a mapping ``name -> plugin_instance``.  The name is the same as
    the dotted import path (used later for lookup).
    """
    plugins_cfg_path = Path(__file__).resolve().parents[3] / "config" / "plugins.yaml"
    if not plugins_cfg_path.is_file():
        raise ConfigError(f"Plugins configuration not found at {plugins_cfg_path}")
    with plugins_cfg_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    plugin_paths: List[str] = data.get("plugins", [])

    registry: Dict[str, Any] = {}
    for path in plugin_paths:
        try:
            attr = _import_attribute(path)
            # If the attribute is a class, instantiate it (no‑arg ctor assumed)
            instance = attr() if callable(attr) else attr
            registry[path] = instance
        except PluginError as exc:
            raise PluginError(f"Failed to load plugin '{path}': {exc}")
    return registry


__all__ = ["load_plugins"]
