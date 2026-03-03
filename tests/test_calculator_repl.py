"""
Tests for the Calculator REPL Module
======================================

Tests the Calculator Facade: input processing, special commands
(help, history, clear, undo, redo, save, load), LBYL validation,
EAFP error handling, and observer/memento integration.
"""

import os
import pytest
from decimal import Decimal
from unittest.mock import patch

from app.calculator_repl import Calculator
from app.exceptions import CalculationError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def env_file(tmp_path):
    """Create a .env file with a temp history path."""
    history_path = str(tmp_path / "history.csv").replace("\\", "/")
    env = tmp_path / ".env"
    env.write_text(
        f"HISTORY_FILE={history_path}\n"
        "AUTO_SAVE=false\n"
        "MAX_HISTORY=100\n"
    )
    return str(env)


@pytest.fixture
def calculator(env_file: str) -> Calculator:
    """Provide a fresh Calculator instance with temp config."""
    return Calculator(env_path=env_file)


# ---------------------------------------------------------------------------
# Arithmetic operations via process_input
# ---------------------------------------------------------------------------


class TestArithmeticOperations:
    """Test that arithmetic commands are processed correctly."""

    @pytest.mark.parametrize(
        "user_input, expected_substring",
        [
            ("add 5 3", "5 + 3 = 8"),
            ("subtract 10 4", "10 - 4 = 6"),
            ("multiply 6 7", "6 * 7 = 42"),
            ("divide 20 4", "20 / 4 = 5"),
            ("power 2 8", "2 ^ 8 = 256"),
            ("root 9 2", "9 √ 2 = 3"),
            ("add -5 3", "-5 + 3 = -2"),
            ("multiply 0 100", "0 * 100 = 0"),
            ("add 1.5 2.5", "1.5 + 2.5 = 4.0"),
            ("sqrt 9", "√(9) = 3"),
            ("cube 3", "3^3 = 27"),
            ("cbrt 27", "³√(27) = 3"),
        ],
        ids=[
            "add", "subtract", "multiply", "divide",
            "power", "root", "negative", "zero", "decimal",
            "sqrt", "cube", "cbrt",
        ],
    )
    def test_valid_operations(
        self, calculator: Calculator, user_input: str, expected_substring: str
    ) -> None:
        """Test that valid operations produce the correct result."""
        result = calculator.process_input(user_input)
        assert expected_substring in result

    def test_operation_adds_to_history(self, calculator: Calculator) -> None:
        """Successful operations are recorded in history."""
        calculator.process_input("add 2 3")
        assert len(calculator.history) == 1


# ---------------------------------------------------------------------------
# Input validation (LBYL)
# ---------------------------------------------------------------------------


class TestInputValidation:
    """Test LBYL input validation."""

    @pytest.mark.parametrize(
        "user_input",
        ["add", "add 5", "add 5 3 2", "5 3", "", "sqrt", "sqrt 9 3"],
        ids=["one_token", "two_tokens", "four_tokens", "missing_op", "empty", "sqrt_no_arg", "sqrt_too_many"],
    )
    def test_invalid_format(self, calculator: Calculator, user_input: str) -> None:
        """Incorrectly formatted input returns an error."""
        result = calculator.process_input(user_input)
        assert "Error" in result or result == ""

    @pytest.mark.parametrize(
        "user_input",
        ["modulo 5 3", "sin 9 0", "log 2 8"],
        ids=["modulo", "sin", "log"],
    )
    def test_unknown_operation(self, calculator: Calculator, user_input: str) -> None:
        """Unknown operations produce a clear error."""
        result = calculator.process_input(user_input)
        assert "Unknown operation" in result


# ---------------------------------------------------------------------------
# Error handling (EAFP)
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Test EAFP error handling for runtime errors."""

    def test_division_by_zero(self, calculator: Calculator) -> None:
        """Division by zero is handled gracefully."""
        result = calculator.process_input("divide 10 0")
        assert "Error" in result

    @pytest.mark.parametrize(
        "user_input",
        ["add abc 3", "add 5 xyz", "add abc xyz", "sqrt abc"],
        ids=["invalid_first", "invalid_second", "both_invalid", "sqrt_invalid"],
    )
    def test_invalid_numbers(self, calculator: Calculator, user_input: str) -> None:
        """Non-numeric inputs are handled gracefully."""
        result = calculator.process_input(user_input)
        assert "not valid numbers" in result

    def test_error_does_not_add_to_history(self, calculator: Calculator) -> None:
        """Failed operations are NOT recorded in history."""
        calculator.process_input("divide 10 0")
        assert len(calculator.history) == 0

    def test_calculation_error_from_factory(self, calculator: Calculator) -> None:
        """CalculationError raised by factory is handled (EAFP)."""
        with patch(
            "app.calculator_repl.CalculationFactory.create",
            side_effect=CalculationError("Injected error"),
        ):
            result = calculator.process_input("add 1 2")
        assert "Error" in result
        assert "Injected error" in result


# ---------------------------------------------------------------------------
# Special commands
# ---------------------------------------------------------------------------


class TestSpecialCommands:
    """Test special (non-arithmetic) commands."""

    def test_help(self, calculator: Calculator) -> None:
        """'help' returns help text."""
        result = calculator.process_input("help")
        assert "Calculator Help" in result
        assert "add" in result
        assert "cube" in result

    def test_help_question_mark(self, calculator: Calculator) -> None:
        """'?' is a shortcut for help."""
        result = calculator.process_input("?")
        assert "Calculator Help" in result

    def test_history_empty(self, calculator: Calculator) -> None:
        """'history' with no calculations returns appropriate message."""
        result = calculator.process_input("history")
        assert "No calculations" in result

    def test_history_with_entries(self, calculator: Calculator) -> None:
        """'history' after calculations shows them."""
        calculator.process_input("add 1 2")
        calculator.process_input("sqrt 9")
        calculator.process_input("multiply 3 4")
        result = calculator.process_input("history")
        assert "add" in result
        assert "sqrt" in result
        assert "multiply" in result
        assert "3 calculation(s)" in result

    def test_clear(self, calculator: Calculator) -> None:
        """'clear' removes all history."""
        calculator.process_input("add 1 2")
        result = calculator.process_input("clear")
        assert "cleared" in result.lower()
        assert len(calculator.history) == 0

    def test_case_insensitive(self, calculator: Calculator) -> None:
        """Commands are case-insensitive."""
        result = calculator.process_input("HELP")
        assert "Calculator Help" in result

    def test_case_insensitive_operations(self, calculator: Calculator) -> None:
        """Operations are case-insensitive."""
        result = calculator.process_input("ADD 5 3")
        assert "5 + 3 = 8" in result


# ---------------------------------------------------------------------------
# Undo / Redo commands
# ---------------------------------------------------------------------------


class TestUndoRedo:
    """Test undo and redo commands."""

    def test_undo_nothing(self, calculator: Calculator) -> None:
        """Undo with nothing to undo."""
        result = calculator.process_input("undo")
        assert "Nothing to undo" in result

    def test_redo_nothing(self, calculator: Calculator) -> None:
        """Redo with nothing to redo."""
        result = calculator.process_input("redo")
        assert "Nothing to redo" in result

    def test_undo_after_calculation(self, calculator: Calculator) -> None:
        """Undo reverts the last calculation."""
        calculator.process_input("add 1 2")
        assert len(calculator.history) == 1
        result = calculator.process_input("undo")
        assert "Undo successful" in result
        assert len(calculator.history) == 0

    def test_redo_after_undo(self, calculator: Calculator) -> None:
        """Redo restores an undone calculation."""
        calculator.process_input("add 1 2")
        calculator.process_input("undo")
        result = calculator.process_input("redo")
        assert "Redo successful" in result
        assert len(calculator.history) == 1

    def test_undo_clear(self, calculator: Calculator) -> None:
        """Undo after clear restores history."""
        calculator.process_input("add 1 2")
        calculator.process_input("clear")
        assert len(calculator.history) == 0
        calculator.process_input("undo")
        assert len(calculator.history) == 1


# ---------------------------------------------------------------------------
# Save / Load commands
# ---------------------------------------------------------------------------


class TestSaveLoad:
    """Test save and load commands."""

    def test_save(self, calculator: Calculator) -> None:
        """'save' writes history to CSV."""
        calculator.process_input("add 1 2")
        result = calculator.process_input("save")
        assert "saved" in result.lower()

    def test_load(self, calculator: Calculator) -> None:
        """'load' reads history from CSV."""
        calculator.process_input("add 1 2")
        calculator.process_input("save")
        calculator.process_input("clear")
        result = calculator.process_input("load")
        assert "Loaded" in result
        assert len(calculator.history) == 1

    def test_load_no_file(self, calculator: Calculator) -> None:
        """'load' when no CSV exists returns 0 loaded."""
        result = calculator.process_input("load")
        assert "0 calculation(s)" in result


# ---------------------------------------------------------------------------
# Auto-save configuration
# ---------------------------------------------------------------------------


class TestAutoSave:
    """Test that auto_save=true registers an AutoSaveObserver."""

    def test_auto_save_observer_registered(self, tmp_path) -> None:
        """When AUTO_SAVE=true, an AutoSaveObserver is added."""
        env = tmp_path / ".env"
        history_path = str(tmp_path / "auto.csv").replace("\\", "/")
        env.write_text(
            f"HISTORY_FILE={history_path}\n"
            "AUTO_SAVE=true\n"
            "MAX_HISTORY=100\n"
        )
        calc = Calculator(env_path=str(env))
        assert hasattr(calc, "auto_save_observer")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


class TestMainEntryPoint:
    """Test the main.py entry point."""

    def test_main_function_exists(self) -> None:
        """main function is importable."""
        from main import main
        assert callable(main)
