"""Shared test configuration and fixtures."""

import pytest
from decimal import Decimal

from app import load_plugins
from app.calculation import Calculation
from app.operations import add, subtract, multiply, divide
from app.command_loader import command_manager
 
@pytest.fixture(scope="session")
def load_app_plugins():
    """Ensure that all plugins are loaded before any tests are run."""
    # Clear any existing commands
    command_manager.clear_commands()
    load_plugins()
 

@pytest.fixture
def sample_add_calc() -> Calculation:
    """Provide a sample addition Calculation."""
    return Calculation(Decimal("5"), Decimal("3"), add, "add")


@pytest.fixture
def sample_subtract_calc() -> Calculation:
    """Provide a sample subtraction Calculation."""
    return Calculation(Decimal("10"), Decimal("4"), subtract, "subtract")
