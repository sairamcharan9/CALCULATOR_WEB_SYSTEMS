"""
Command Management and Registration
===================================

This module implements a dynamic command registration system using the
Decorator design pattern. It allows for easy extension by enabling commands
to be registered from different parts of the application, including external plugins.

The `CommandManager` class acts as a central registry for all commands, mapping
command names to their corresponding handler functions, descriptions, and usage instructions.

Key Components:
- Command: A named tuple to store command metadata.
- CommandManager: A singleton class to register and retrieve commands.

The `register_command` decorator simplifies the process of adding new commands
to the system.
"""

import logging
from typing import Callable, NamedTuple, Optional, List

from app.logger import get_logger

# Initialize the logger for this module
_log: logging.Logger = get_logger("commands")


class Command(NamedTuple):
    """
    A named tuple representing a command with its metadata.

    Attributes:
        name (str): The primary name of the command.
        handler (Callable): The function that executes the command's logic.
        description (str): A brief description of what the command does.
        usage (str): Instructions on how to use the command, including aliases.
    """
    name: str
    handler: Callable
    description: str
    usage: str


class CommandManager:
    """
    A singleton class that manages the registration and retrieval of commands.

    This class provides a central registry for all commands in the application.
    It supports registering commands, retrieving them, and getting a list of
    all registered command names.

    Attributes:
        _instance (Optional[CommandManager]): The singleton instance of the class.
        commands (dict[str, Command]): A dictionary mapping command names to Command objects.
    """
    _instance: Optional['CommandManager'] = None

    def __new__(cls) -> 'CommandManager':
        """
        Ensures that only one instance of CommandManager is created.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.commands = {}
            _log.info("CommandManager initialized.")
        return cls._instance

    def register(self, command_name: str, handler: Callable, description: str, usage: str) -> None:
        """
        Registers a new command or updates an existing one.

        Args:
            command_name (str): The name of the command to register.
            handler (Callable): The function to execute for this command.
            description (str): A description of the command for the help menu.
            usage (str): The usage string for the command.
        """
        if command_name in self.commands:
            _log.warning("Command '%s' is being overridden.", command_name)
        self.commands[command_name] = Command(command_name, handler, description, usage)
        _log.info("Command '%s' registered.", command_name)

    def get_command(self, command_name: str) -> Optional[Command]:
        """
        Retrieves a command by its name.

        Args:
            command_name (str): The name of the command to retrieve.

        Returns:
            Optional[Command]: The Command object if found, otherwise None.
        """
        return self.commands.get(command_name)

    def get_all_commands(self) -> List[Command]:
        """
        Retrieves a sorted list of all registered commands.

        Returns:
            List[Command]: A list of all Command objects, sorted by name.
        """
        return sorted(self.commands.values(), key=lambda cmd: cmd.name)

    def clear_commands(self) -> None:
        """Clears all registered commands."""
        self.commands = {}
        _log.info("All commands cleared.")


def command(command_name: str, description: str, usage: str) -> Callable:
    """
    A decorator to register a command with the CommandManager.

    Args:
        command_name (str): The name of the command to register.
        description (str): A brief description of the command for the help menu.
        usage (str): A string showing how to use the command (e.g., 'add <n1> <n2>').

    Returns:
        Callable: The decorator that registers the function.
    """
    from app.command_loader import command_manager
    def decorator(handler: Callable) -> Callable:
        command_manager.register(command_name, handler, description, usage)
        return handler
    return decorator

# This is a test comment to force a git change.
