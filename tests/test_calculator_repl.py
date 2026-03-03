"""
Integration Tests for the Calculator REPL
==========================================

Tests for the Calculator facade class, covering:
- Configuration loading
- Command processing (arithmetic and special commands)
- Observer integration
- Error handling
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from app.calculator_repl import Calculator
from app.exceptions import CalculationError


@pytest.fixture
def calculator(tmp_path):
    """Provide a Calculator instance configured for testing."""
    env = tmp_path / ".env"
    env.write_text(
        f"CALCULATOR_LOG_DIR={tmp_path}/logs\n"
        f"CALCULATOR_HISTORY_DIR={tmp_path}/data\n"
        "CALCULATOR_AUTO_SAVE=true\n"
        "CALCULATOR_PRECISION=2\n"
    )
    return Calculator(env_path=str(env))


class TestCalculatorREPL:
    """Integration tests for the Calculator REPL."""

    def test_process_input_arithmetic(self, calculator: Calculator) -> None:
        """Arithmetic commands compute correctly and add to history."""
        result = calculator.process_input("add 5 3")
        assert "8.00" in result
        assert len(calculator.history) == 1

    def test_process_input_special_commands(self, calculator: Calculator) -> None:
        """Special commands return expected output."""
        assert "Calculator Help" in calculator.process_input("help")

        calculator.process_input("add 1 1")
        assert "Calculation History" in calculator.process_input("history")

        assert "History cleared" in calculator.process_input("clear")
        assert len(calculator.history) == 0

    def test_undo_redo(self, calculator: Calculator) -> None:
        """Undo and redo commands work through the caretaker."""
        calculator.process_input("add 5 3")
        assert len(calculator.history) == 1

        calculator.process_input("undo")
        assert len(calculator.history) == 0

        calculator.process_input("redo")
        assert len(calculator.history) == 1

    def test_invalid_input(self, calculator: Calculator) -> None:
        """Invalid commands/operands return error messages."""
        assert "Unknown operation" in calculator.process_input("unknown 1 2")
        assert "not a valid number" in calculator.process_input("add abc 1")

    def test_save_load(self, calculator: Calculator) -> None:
        """Manual save and load commands work."""
        calculator.process_input("add 10 5")
        assert "History saved" in calculator.process_input("save")

        calculator.process_input("clear")
        assert len(calculator.history) == 0

        assert "Loaded 1" in calculator.process_input("load")
        assert len(calculator.history) == 1
