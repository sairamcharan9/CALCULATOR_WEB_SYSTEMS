"""
Greet Command Plugin
====================

This plugin provides a simple 'greet' command to demonstrate the extensibility
of the command system.
"""

from colorama import Fore
from app.commands import command


@command("greet", "Display a greeting.", "greet")
def greet_command(*args, **kwargs) -> str:
    """Displays a simple greeting message."""
    msg = "Hello! Welcome to the calculator."
    print(f"{Fore.MAGENTA}{msg}")
    return msg
