"""
Tests for the Logging Module and Integration
===========================================

This module contains tests for the centralized logging setup, including
configuration, reconfiguration, and integration with other components like
the `LoggingObserver` and the main `Calculator` REPL.
"""

import pytest
import logging
import os
from unittest.mock import patch, MagicMock
from decimal import Decimal

from app import load_plugins
from app.calculator_repl import Calculator
from app.calculation import Calculation
from app.history import LoggingObserver, CalculationHistory

load_plugins()

# Dummy operation for creating Calculation instances
def dummy_op(a, b): return a + b

# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture(autouse=True)
def manage_logging_for_tests(tmp_path):
    """
    Fixture to set up and tear down logging for each test.
    This ensures that tests do not interfere with each other's logging state.
    """
    from app.logger import reconfigure_logging, _is_configured
    
    # Store original state
    original_is_configured = _is_configured
    original_handlers = logging.getLogger("calculator").handlers[:]
    
    # Configure logging for the test
    log_dir = tmp_path / "logs"
    log_file = log_dir / "test.log"
    reconfigure_logging(log_dir=str(log_dir), log_file=str(log_file), encoding="utf-8")
    
    yield  # Run the test
    
    # --- Teardown ---
    # 1. Get the logger and its handlers
    logger = logging.getLogger("calculator")
    handlers = logger.handlers[:]
    
    # 2. Close and remove each handler
    for handler in handlers:
        handler.close()
        logger.removeHandler(handler)
        
    # 3. Reset the configuration flag in the logger module
    import app.logger
    app.logger._is_configured = original_is_configured
    
    # 4. Restore original handlers if any
    for handler in original_handlers:
        logger.addHandler(handler)


@pytest.fixture
def calculator_for_logging(tmp_path):
    """Provides a Calculator instance with a dedicated log file for testing REPL logging."""
    env_path = tmp_path / ".env"
    env_path.write_text(
        f"CALCULATOR_LOG_DIR={tmp_path}/logs\n"
        f"CALCULATOR_LOG_FILE=repl_test.log\n"
        f"CALCULATOR_HISTORY_DIR={tmp_path}/data\n"
        "CALCULATOR_AUTO_SAVE=false\n"
    )
    return Calculator(env_path=str(env_path))


# ===========================================================================
# Test Cases
# ===========================================================================

class TestConfigureLogging:
    """Tests for the initial logger configuration."""

    def test_creates_log_file(self, tmp_path):
        """Log file and directory should be created if they don't exist."""
        log_dir = tmp_path / "new_logs"
        log_file = log_dir / "app.log"
        from app.logger import reconfigure_logging
        reconfigure_logging(log_dir=str(log_dir), log_file=str(log_file), encoding="utf-8")
        assert log_dir.exists()
        assert log_file.exists()

    def test_idempotent(self, tmp_path):
        """Calling configure multiple times should not add duplicate handlers."""
        from app.logger import configure_logging
        import app.logger
        
        # Clear existing handlers from fixture to start with a clean slate
        root = logging.getLogger("calculator")
        for h in root.handlers[:]:
            h.close()
            root.removeHandler(h)
        
        app.logger._is_configured = False # Reset for this specific test
        
        log_dir = str(tmp_path / "logs")
        configure_logging(log_dir=log_dir, log_file="app.log")
        configure_logging(log_dir=log_dir, log_file="app.log")
        
        # Should still be exactly 1 handler (file)
        assert len(root.handlers) == 1

    def test_file_handler_present(self):
        """The root logger should have a FileHandler."""
        handlers = logging.getLogger("calculator").handlers
        assert any(isinstance(h, logging.FileHandler) for h in handlers)



class TestReconfigureLogging:
    """Tests for reconfiguring an existing logger setup."""

    def test_switches_log_file(self, tmp_path):
        """Reconfiguring should close old handlers and use the new file."""
        from app.logger import reconfigure_logging
        
        # Initial config
        log_file1 = tmp_path / "log1.log"
        reconfigure_logging(log_dir=str(tmp_path), log_file=str(log_file1), encoding="utf-8")
        logging.getLogger("calculator").info("Message 1")

        # Reconfigure to a new file
        log_file2 = tmp_path / "log2.log"
        reconfigure_logging(log_dir=str(tmp_path), log_file=str(log_file2), encoding="utf-8")
        logging.getLogger("calculator").info("Message 2")

        # Verify content of log files
        assert "Message 1" in log_file1.read_text()
        assert "Message 2" in log_file2.read_text()
        assert "Message 2" not in log_file1.read_text()

    def test_handler_count_remains_two(self, tmp_path):
        """Reconfiguring should not add duplicate handlers."""
        from app.logger import reconfigure_logging
        logger = logging.getLogger("calculator")
        
        reconfigure_logging(log_dir=str(tmp_path), log_file="f1.log", encoding="utf-8")
        assert len(logger.handlers) == 1
        
        reconfigure_logging(log_dir=str(tmp_path), log_file="f2.log", encoding="utf-8")
        assert len(logger.handlers) == 1


class TestGetLogger:
    """Tests for the get_logger utility function."""

    def test_returns_child_logger(self):
        """get_logger should return a logger that is a child of 'calculator'."""
        from app.logger import get_logger
        child_logger = get_logger("my_module")
        assert child_logger.name == "calculator.my_module"

    def test_child_logger_inherits_parent(self):
        """The child logger should inherit handlers from the parent."""
        from app.logger import get_logger
        parent_logger = logging.getLogger("calculator")
        child_logger = get_logger("child")
        assert child_logger.propagate is True
        assert len(child_logger.handlers) == 0  # Should not have its own handlers
        assert len(parent_logger.handlers) > 0


class TestLoggingObserverIntegration:
    """Tests the LoggingObserver's interaction with the logging system."""

    def test_observer_logs_to_file(self, tmp_path, sample_add_calc):
        """The LoggingObserver should write to the configured log file."""
        log_file = tmp_path / "observer_test.log"
        from app.logger import reconfigure_logging
        reconfigure_logging(log_dir=str(tmp_path), log_file=str(log_file), encoding="utf-8")

        history = CalculationHistory()
        observer = LoggingObserver()
        history.add_observer(observer)
        
        calc = Calculation(Decimal("10"), Decimal("5"), dummy_op, "add")
        history.add(calc)
        
        # Verify that the log file contains the output
        log_content = log_file.read_text()
        assert "New calculation recorded" in log_content
        assert "10 + 5 = 15.00" in log_content

    def test_observer_uses_info_level(self):
        """The observer should log at the INFO level."""
        with patch.object(logging.getLogger("calculator.history"), 'info') as mock_info:
            observer = LoggingObserver()
            calc = Calculation(Decimal("1"), Decimal("1"), dummy_op, "add")
            observer.on_calculation(calc)
            mock_info.assert_called_once()


class TestREPLLogging:
    """Integration tests for logging within the Calculator REPL."""

    def test_successful_calculation_logged_info(self, calculator_for_logging, tmp_path):
        """A successful calculation should be logged at INFO level."""
        calculator_for_logging.process_input("add 3 4")
        log_file = tmp_path / "logs" / "repl_test.log"
        content = log_file.read_text()
        assert "Calculation successful" in content
        assert "3 + 4 = 7.00" in content

    def test_failed_calculation_logged_error(self, calculator_for_logging, tmp_path):
        """A failed calculation should be logged at ERROR level."""
        calculator_for_logging.process_input("divide 5 0")
        log_file = tmp_path / "logs" / "repl_test.log"
        content = log_file.read_text()
        assert "ERROR" in content
        assert "Calculation error" in content
        assert "Cannot divide by zero" in content

    def test_invalid_input_logged_warning(self, calculator_for_logging, tmp_path):
        """User input that fails validation should be logged at WARNING level."""
        calculator_for_logging.process_input("add invalid 1")
        log_file = tmp_path / "logs" / "repl_test.log"
        content = log_file.read_text()
        assert "WARNING" in content
        assert "Invalid number input" in content

    def test_undo_logged(self, calculator_for_logging, tmp_path):
        """An undo action should be logged."""
        calculator_for_logging.process_input("add 1 1")
        calculator_for_logging.process_input("undo")
        log_file = tmp_path / "logs" / "repl_test.log"
        content = log_file.read_text()
        assert "Undo successful" in content

    def test_save_logged(self, calculator_for_logging, tmp_path):
        """A manual save action should be logged."""
        calculator_for_logging.process_input("add 2 2")
        calculator_for_logging.process_input("save")
        log_file = tmp_path / "logs" / "repl_test.log"
        content = log_file.read_text()
        assert "History manually saved" in content
