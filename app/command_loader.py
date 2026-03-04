"""
Command Loader
==============

This module provides a singleton instance of the CommandManager.
"""

from app.commands import CommandManager

# It is crucial to import app.operations here. This ensures that all functions
# decorated with @command in app.operations are registered with the CommandManager
# at application startup. Without this import, the commands defined in app.operations
# would not be discoverable or executable by the REPL.
import app.operations  # pylint: disable=unused-import

command_manager = CommandManager()
