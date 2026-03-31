"""
Tests for the Command Management System
=======================================

This module contains tests for the command registration and management
system, including the `CommandManager`, the `@command` decorator,
and the dynamic loading of plugins.
"""

import pytest
from app import load_plugins
from app.command_loader import command_manager
from app.plugins.greet import greet_command

@pytest.fixture(autouse=True)
def setup_teardown():
    command_manager.clear_commands()
    load_plugins()

# A simple handler function for testing
def mock_handler(*args, **kwargs):
    return "mock handler executed"

def test_command_manager_singleton():
    """Verify that the CommandManager is a singleton."""
    from app.command_loader import command_manager as cm1
    from app.command_loader import command_manager as cm2
    assert cm1 is cm2, "CommandManager should be a singleton"

def test_register_and_get_command():
    """Test registering a new command and retrieving it."""
    # Register a test command
    command_manager.register("test", mock_handler, "A test command", "test <arg>")
    
    # Retrieve the command
    command = command_manager.get_command("test")
    
    assert command is not None, "Command should be found after registration"
    assert command.name == "test"
    assert command.handler == mock_handler
    assert command.description == "A test command"
    assert command.usage == "test <arg>"

def test_get_nonexistent_command():
    """Test that getting a nonexistent command returns None."""
    assert command_manager.get_command("nonexistent") is None

def test_get_all_commands():
    """Test retrieving all registered commands."""
    # Clear existing commands for a clean test
    command_manager.clear_commands()
    
    # Register a few commands
    command_manager.register("cmd1", mock_handler, "desc1", "usage1")
    command_manager.register("cmd2", mock_handler, "desc2", "usage2")
    
    all_commands = command_manager.get_all_commands()
    
    assert len(all_commands) == 2, "Should return all registered commands"
    assert all_commands[0].name == "cmd1"
    assert all_commands[1].name == "cmd2"

def test_register_command_decorator():
    """Test that the @command decorator correctly registers a command."""
    # The 'greet' command is registered via decorator in the plugin
    greet_cmd = command_manager.get_command("greet")
    
    assert greet_cmd is not None, "Decorator should register the command"
    assert greet_cmd.name == "greet"
    assert greet_cmd.handler.__name__ == greet_command.__name__
    assert greet_cmd.description == "Display a greeting."
    assert greet_cmd.usage == "greet"

def test_plugin_loading_mechanism():
    """
    Test that plugins are loaded and their commands are registered.
    
    This test relies on the `app/__init__.py` automatically loading plugins.
    """
    # Check if a command from a plugin is registered
    # The 'add' command is in operations.py, which now acts like a plugin
    add_cmd = command_manager.get_command("add")
    assert add_cmd is not None, "Commands from operations.py should be loaded"

    # The 'history' command is in a dedicated plugin file
    history_cmd = command_manager.get_command("history")
    assert history_cmd is not None, "Commands from plugin files should be loaded"
