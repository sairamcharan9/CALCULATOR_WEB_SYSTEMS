"""
Command Management and Registration
===================================

Implements a dynamic command registration system using the Decorator design
pattern. Allows commands to be registered from different parts of the
application, including external plugins.
"""

import logging
from typing import Callable, NamedTuple, Optional, List

from app.core.logger import get_logger

# Initialize the logger for this module
_log: logging.Logger = get_logger("commands")


class Command(NamedTuple):
    """
    A named tuple representing a command with its metadata.

    Attributes:
        name (str): The primary name of the command.
        handler (Callable): The function that executes the command's logic.
        description (str): A brief description of what the command does.
        usage (str): Instructions on how to use the command.
    """
    name: str
    handler: Callable
    description: str
    usage: str


class CommandManager:
    """
    A singleton class that manages the registration and retrieval of commands.
    """
    _instance: Optional['CommandManager'] = None

    def __new__(cls) -> 'CommandManager':
        """Ensures that only one instance of CommandManager is created."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.commands = {}
            cls._instance._sorted_commands_cache = None
            _log.info("CommandManager initialized.")
        return cls._instance

    def register(self, command_name: str, handler: Callable, description: str, usage: str) -> None:
        """Registers a new command or updates an existing one."""
        if command_name in self.commands:
            _log.warning("Command '%s' is being overridden.", command_name)
        self.commands[command_name] = Command(command_name, handler, description, usage)
        self._sorted_commands_cache = None
        _log.info("Command '%s' registered.", command_name)

    def get_command(self, command_name: str) -> Optional[Command]:
        """Retrieves a command by its name."""
        return self.commands.get(command_name)

    def get_all_commands(self) -> List[Command]:
        """Retrieves a sorted list of all registered commands."""
        if self._sorted_commands_cache is None:
            self._sorted_commands_cache = sorted(self.commands.values(), key=lambda cmd: cmd.name)
        return list(self._sorted_commands_cache)

    def clear_commands(self) -> None:
        """Clears all registered commands."""
        self.commands = {}
        self._sorted_commands_cache = None
        _log.info("All commands cleared.")


def command(command_name: str, description: str, usage: str) -> Callable:
    """
    A decorator to register a command with the CommandManager.

    Args:
        command_name (str): The name of the command to register.
        description (str): A brief description of the command for the help menu.
        usage (str): A string showing how to use the command.

    Returns:
        Callable: The decorator that registers the function.
    """
    from app.cli.command_loader import command_manager

    def decorator(handler: Callable) -> Callable:
        command_manager.register(command_name, handler, description, usage)
        return handler
    return decorator
