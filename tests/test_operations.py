"""
Tests for the Operations Module
================================

Parameterized tests covering mandatory arithmetic operations:
add, subtract, multiply, divide, power, root, modulus, int_divide,
percent, abs_diff — including edge cases.
"""

import pytest
from decimal import Decimal

from app import load_plugins
from app.command_loader import command_manager
from app.exceptions import DivisionByZeroError, InvalidOperationError
from app.operations import (
    add,
    subtract,
    multiply,
    divide,
    nth_power,
    nth_root,
    modulus,
    int_divide,
    percent,
    abs_diff,
)

@pytest.fixture(autouse=True)
def setup_teardown():
    command_manager.clear_commands()
    load_plugins()

# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("2"), Decimal("3"), Decimal("5")),
        (Decimal("0"), Decimal("0"), Decimal("0")),
        (Decimal("-1"), Decimal("1"), Decimal("0")),
        (Decimal("-5"), Decimal("-3"), Decimal("-8")),
        (Decimal("1.5"), Decimal("2.5"), Decimal("4.0")),
    ],
)
def test_add(a: Decimal, b: Decimal, expected: Decimal) -> None:
    assert add(a, b) == expected


# ---------------------------------------------------------------------------
# subtract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("5"), Decimal("3"), Decimal("2")),
        (Decimal("0"), Decimal("0"), Decimal("0")),
        (Decimal("3"), Decimal("5"), Decimal("-2")),
    ],
)
def test_subtract(a: Decimal, b: Decimal, expected: Decimal) -> None:
    assert subtract(a, b) == expected


# ---------------------------------------------------------------------------
# multiply
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("4"), Decimal("3"), Decimal("12")),
        (Decimal("0"), Decimal("100"), Decimal("0")),
        (Decimal("-2"), Decimal("3"), Decimal("-6")),
    ],
)
def test_multiply(a: Decimal, b: Decimal, expected: Decimal) -> None:
    assert multiply(a, b) == expected


# ---------------------------------------------------------------------------
# divide
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("10"), Decimal("2"), Decimal("5")),
        (Decimal("7"), Decimal("2"), Decimal("3.5")),
    ],
)
def test_divide(a: Decimal, b: Decimal, expected: Decimal) -> None:
    assert divide(a, b) == expected


def test_divide_by_zero() -> None:
    with pytest.raises(DivisionByZeroError):
        divide(Decimal("10"), Decimal("0"))


# ---------------------------------------------------------------------------
# nth_power
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("2"), Decimal("8"), Decimal("256")),
        (Decimal("5"), Decimal("0"), Decimal("1")),
    ],
)
def test_nth_power(a: Decimal, b: Decimal, expected: Decimal) -> None:
    assert nth_power(a, b) == expected


# ---------------------------------------------------------------------------
# nth_root
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("9"), Decimal("2"), Decimal("3")),
        (Decimal("27"), Decimal("3"), Decimal("3")),
    ],
)
def test_nth_root(a: Decimal, b: Decimal, expected: Decimal) -> None:
    assert nth_root(a, b) == expected


def test_root_by_zero() -> None:
    with pytest.raises(DivisionByZeroError):
        nth_root(Decimal("9"), Decimal("0"))


# ---------------------------------------------------------------------------
# modulus
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("10"), Decimal("3"), Decimal("1")),
        (Decimal("10"), Decimal("2"), Decimal("0")),
    ],
)
def test_modulus(a: Decimal, b: Decimal, expected: Decimal) -> None:
    assert modulus(a, b) == expected


def test_modulus_by_zero() -> None:
    with pytest.raises(DivisionByZeroError):
        modulus(Decimal("10"), Decimal("0"))


# ---------------------------------------------------------------------------
# int_divide
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("10"), Decimal("3"), Decimal("3")),
        (Decimal("10"), Decimal("2"), Decimal("5")),
    ],
)
def test_int_divide(a: Decimal, b: Decimal, expected: Decimal) -> None:
    assert int_divide(a, b) == expected


def test_int_divide_by_zero() -> None:
    with pytest.raises(DivisionByZeroError):
        int_divide(Decimal("10"), Decimal("0"))


# ---------------------------------------------------------------------------
# percent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("5"), Decimal("100"), Decimal("5")),
        (Decimal("50"), Decimal("200"), Decimal("25")),
    ],
)
def test_percent(a: Decimal, b: Decimal, expected: Decimal) -> None:
    assert percent(a, b) == expected


def test_percent_by_zero() -> None:
    with pytest.raises(DivisionByZeroError):
        percent(Decimal("10"), Decimal("0"))


# ---------------------------------------------------------------------------
# abs_diff
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (Decimal("5"), Decimal("10"), Decimal("5")),
        (Decimal("10"), Decimal("5"), Decimal("5")),
        (Decimal("-5"), Decimal("5"), Decimal("10")),
    ],
)
def test_abs_diff(a: Decimal, b: Decimal, expected: Decimal) -> None:
    assert abs_diff(a, b) == expected


# ---------------------------------------------------------------------------
# Command Registration
# ---------------------------------------------------------------------------


class TestOperationRegistration:
    
    ARITHMETIC_COMMANDS = [
        "add", "subtract", "multiply", "divide", "power", "root", 
        "modulus", "int_divide", "percent", "abs_diff"
    ]

    @pytest.mark.parametrize("command_name", ARITHMETIC_COMMANDS)
    def test_arithmetic_commands_are_registered(self, command_name: str):
        """Verify that all arithmetic operations are registered as commands."""
        command = command_manager.get_command(command_name)
        assert command is not None, f"Command '{command_name}' should be registered."
        assert callable(command.handler), f"Handler for '{command_name}' should be callable."
