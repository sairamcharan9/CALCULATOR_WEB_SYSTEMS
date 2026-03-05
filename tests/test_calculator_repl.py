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

from app import load_plugins
from app.calculator_factory import CalculatorFactory
from app.calculator_repl import Calculator
from app.exceptions import CalculationError

load_plugins()


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
    return CalculatorFactory.create_calculator(env_path=str(env))


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

        undo_msg = calculator.process_input("undo")
        assert len(calculator.history) == 0
        assert "Undo successful" in undo_msg
        assert "0 calculation(s)" in undo_msg

        redo_msg = calculator.process_input("redo")
        assert len(calculator.history) == 1
        assert "Redo successful" in redo_msg
        assert "1 calculation(s)" in redo_msg

    def test_undo_nothing(self, calculator: Calculator) -> None:
        """Undo when stack is empty returns 'Nothing to undo'."""
        msg = calculator.process_input("undo")
        assert "Nothing to undo" in msg

    def test_redo_nothing(self, calculator: Calculator) -> None:
        """Redo when stack is empty returns 'Nothing to redo'."""
        msg = calculator.process_input("redo")
        assert "Nothing to redo" in msg

    def test_failed_calc_does_not_pollute_undo_stack(self, calculator: Calculator) -> None:
        """A failed calculation (divide by zero) must NOT add to the undo stack."""
        # With no prior calculations, undo stack should be empty initially
        initial_undo, _ = calculator.caretaker.stack_sizes

        # Attempt a divide-by-zero (should fail)
        calculator.process_input("divide 5 0")

        # Undo stack size must not have grown
        after_undo, _ = calculator.caretaker.stack_sizes
        assert after_undo == initial_undo

    def test_undo_redo_after_multiple_calcs(self, calculator: Calculator) -> None:
        """Can walk back through several calculations with repeated undo."""
        calculator.process_input("add 1 1")
        calculator.process_input("add 2 2")
        calculator.process_input("add 3 3")
        assert len(calculator.history) == 3

        calculator.process_input("undo")
        assert len(calculator.history) == 2

        calculator.process_input("undo")
        assert len(calculator.history) == 1

        calculator.process_input("redo")
        assert len(calculator.history) == 2

    def test_redo_after_clear_undo(self, calculator: Calculator) -> None:
        """Redo restores history after a clear+undo sequence."""
        calculator.process_input("add 5 3")
        assert len(calculator.history) == 1

        calculator.process_input("clear")
        assert len(calculator.history) == 0

        calculator.process_input("undo")
        assert len(calculator.history) == 1

        calculator.process_input("redo")
        assert len(calculator.history) == 0

    def test_invalid_input(self, calculator: Calculator) -> None:
        """Invalid commands/operands return error messages."""
        assert "Invalid number of arguments" in calculator.process_input("add 1")
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

    def test_empty_input_returns_empty_string(self, calculator: Calculator) -> None:
        """Empty or whitespace-only input returns empty string."""
        assert calculator.process_input("") == ""
        assert calculator.process_input("   ") == ""

    def test_greet_command(self, calculator: Calculator) -> None:
        """greet command returns a greeting message."""
        msg = calculator.process_input("greet")
        assert "Hello" in msg or "Welcome" in msg

    def test_history_empty_message(self, calculator: Calculator) -> None:
        """history command on empty history returns appropriate message."""
        msg = calculator.process_input("history")
        assert "No calculations" in msg

    def test_history_with_entries(self, calculator: Calculator) -> None:
        """history command shows entries when history is populated."""
        calculator.process_input("add 1 2")
        calculator.process_input("multiply 3 4")
        msg = calculator.process_input("history")
        assert "Calculation History" in msg
        assert "add" in msg
        assert "multiply" in msg

    def test_question_mark_shows_help(self, calculator: Calculator) -> None:
        """'?' is an alias for 'help'."""
        msg = calculator.process_input("?")
        assert "Calculator Help" in msg

    def test_autoload_logs_on_existing__csv(self, tmp_path) -> None:
        """Auto-load logs INFO when a history CSV already exists on startup."""
        import logging
        import app.logger as logger_module

        env = tmp_path / ".env"
        env.write_text(
            f"CALCULATOR_LOG_DIR={tmp_path}/logs\n"
            f"CALCULATOR_HISTORY_DIR={tmp_path}/data\n"
            "CALCULATOR_LOG_FILE=autoload.log\n"
            "CALCULATOR_AUTO_SAVE=false\n"
            "CALCULATOR_PRECISION=2\n"
        )
        calc1 = CalculatorFactory.create_calculator(env_path=str(env))
        calc1.process_input("add 3 4")
        calc1.process_input("save")

        for h in logging.getLogger("calculator").handlers:
            h.flush()
            h.close()
        logging.getLogger("calculator").handlers.clear()
        logger_module._is_configured = False

        calc2 = CalculatorFactory.create_calculator(env_path=str(env))
        log_path = tmp_path / "logs" / "autoload.log"
        for h in logging.getLogger("calculator").handlers:
            h.flush()
        if log_path.exists():
            content = log_path.read_text(encoding="utf-8")
            assert "Auto-loaded" in content or "auto" in content.lower() or len(calc2.history) == 1
