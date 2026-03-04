"""
Application Package Initialization
================================

This module initializes the application package and dynamically loads all plugins
from the `app.plugins` directory. This dynamic loading mechanism is crucial for
the extensibility of the application, allowing new commands to be added by simply
creating a new Python file in the plugins directory.

The `load_plugins` function iterates over all modules in the `app.plugins` package,
importing them to ensure that any commands registered with the `@command`
decorator are recognized by the `CommandManager`.

This approach ensures that the core application does not need to be modified
to add new functionality.
"""

import os
import importlib
import sys
import logging

from app.logger import get_logger

# Initialize the logger for this module
_log: logging.Logger = get_logger(__name__)


def load_plugins() -> None:
    """
    Dynamically discovers and loads all plugins from the `app.plugins` directory.

    This function iterates through the files in the `app/plugins` directory,
    and for each Python file, it constructs the module name and imports it.
    This process triggers the registration of any commands defined in the plugin
    files via the `@command` decorator.
    """
    # Load arithmetic operations
    module_name = "app.operations"
    try:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)
        _log.info("Successfully loaded arithmetic operations.")
    except ImportError as e:
        _log.error("Failed to load arithmetic operations: %s", e)
        
    plugins_dir = os.path.dirname(__file__) + "/plugins"
    _log.info("Searching for plugins in: %s", plugins_dir)

    for filename in os.listdir(plugins_dir):
        # We are only interested in Python files, and we want to exclude __init__.py
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = f"app.plugins.{filename[:-3]}"
            try:
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                else:
                    importlib.import_module(module_name)
                _log.info("Successfully loaded plugin: %s", module_name)
            except ImportError as e:
                _log.error("Failed to load plugin %s: %s", module_name, e)


# --- Application-wide Plugin Loading ---
# Automatically load all plugins when the application package is imported.
# This ensures that all commands are registered before the application starts.
load_plugins()
