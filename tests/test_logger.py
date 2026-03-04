"""
Tests for the Logging Module
==============================

Tests for configure_logging(), reconfigure_logging(), get_logger(),
and the LoggingObserver integration with the centralized logger.
"""

import logging
import os

import pytest
from decimal import Decimal

from app.calculation import Calculation
from app.operations import add, multiply
from app.history import LoggingObserver, CalculationHistory
import app.logger as logger_module


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_logger():
    """Reset the centralized logger state before and after every test."""
    # Tear down any existing handlers on the root calculator logger
    root = logging.getLogger("calculator")
    for h in root.handlers[:]:
        h.close()
        root.removeHandler(h)
    logger_module._is_configured = False
    yield
    # Teardown again after test
    for h in root.handlers[:]:
        h.close()
        root.removeHandler(h)
    logger_module._is_configured = False


@pytest.fixture
def log_path(tmp_path) -> str:
    """Return a temp log file path and configure logging there."""
    log_dir = str(tmp_path / "logs")
    log_file = "test.log"
    logger_module.configure_logging(log_dir=log_dir, log_file=log_file)
    return os.path.join(log_dir, log_file)


@pytest.fixture
def sample_calc() -> Calculation:
    return Calculation(Decimal("4"), Decimal("5"), multiply, "multiply", precision=2)


# ---------------------------------------------------------------------------
# configure_logging
# ---------------------------------------------------------------------------


class TestConfigureLogging:
    """Tests for configure_logging()."""

    def test_creates_log_file(self, tmp_path) -> None:
        """configure_logging creates the log file on disk."""
        log_dir = str(tmp_path / "logs")
        logger_module.configure_logging(log_dir=log_dir, log_file="app.log")
        assert os.path.exists(os.path.join(log_dir, "app.log"))

    def test_idempotent(self, tmp_path) -> None:
        """Calling configure_logging twice does not add duplicate handlers."""
        log_dir = str(tmp_path / "logs")
        logger_module.configure_logging(log_dir=log_dir, log_file="app.log")
        logger_module.configure_logging(log_dir=log_dir, log_file="app.log")
        root = logging.getLogger("calculator")
        # Should still be exactly 2 handlers (file + stream)
        assert len(root.handlers) == 2

    def test_file_handler_present(self, log_path) -> None:
        """Root calculator logger has a FileHandler attached."""
        root = logging.getLogger("calculator")
        file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1

    def test_stream_handler_present(self, log_path) -> None:
        """Root calculator logger has a StreamHandler attached."""
        root = logging.getLogger("calculator")
        stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)
                           and not isinstance(h, logging.FileHandler)]
        assert len(stream_handlers) == 1


# ---------------------------------------------------------------------------
# reconfigure_logging
# ---------------------------------------------------------------------------


class TestReconfigureLogging:
    """Tests for reconfigure_logging()."""

    def test_switches_log_file(self, tmp_path) -> None:
        """reconfigure_logging switches the active log file."""
        log_dir = str(tmp_path / "logs")
        logger_module.configure_logging(log_dir=log_dir, log_file="first.log")
        logger_module.reconfigure_logging(log_dir=log_dir, log_file="second.log")
        assert os.path.exists(os.path.join(log_dir, "second.log"))

    def test_handler_count_remains_two(self, tmp_path) -> None:
        """After reconfigure, handler count is still 2."""
        log_dir = str(tmp_path / "logs")
        logger_module.configure_logging(log_dir=log_dir, log_file="a.log")
        logger_module.reconfigure_logging(log_dir=log_dir, log_file="b.log")
        root = logging.getLogger("calculator")
        assert len(root.handlers) == 2


# ---------------------------------------------------------------------------
# get_logger
# ---------------------------------------------------------------------------


class TestGetLogger:
    """Tests for get_logger()."""

    def test_returns_child_logger(self) -> None:
        """get_logger('repl') returns a logger named 'calculator.repl'."""
        log = logger_module.get_logger("repl")
        assert log.name == "calculator.repl"

    def test_child_logger_inherits_parent(self, log_path) -> None:
        """Child logger messages propagate to the root 'calculator' logger."""
        log = logger_module.get_logger("test_child")
        # Should not raise; message should reach file handler
        log.info("Test message from child logger.")


# ---------------------------------------------------------------------------
# LoggingObserver integration
# ---------------------------------------------------------------------------


class TestLoggingObserverIntegration:
    """Tests for LoggingObserver using the centralized logger."""

    def test_observer_logs_to_file(self, tmp_path, sample_calc) -> None:
        """LoggingObserver writes a calculation entry to the log file."""
        log_dir = str(tmp_path / "logs")
        log_file = "calc.log"
        logger_module.configure_logging(log_dir=log_dir, log_file=log_file)

        observer = LoggingObserver(log_dir=log_dir, log_file=log_file)
        observer.on_calculation(sample_calc)

        # Flush all handlers
        for h in logging.getLogger("calculator").handlers:
            h.flush()

        log_path = os.path.join(log_dir, log_file)
        content = open(log_path, encoding="utf-8").read()
        assert "4 * 5 = 20.00" in content

    def test_observer_uses_info_level(self, tmp_path, sample_calc) -> None:
        """LoggingObserver messages are emitted at INFO level."""
        log_dir = str(tmp_path / "logs")
        log_file = "info_check.log"
        logger_module.configure_logging(log_dir=log_dir, log_file=log_file, level=logging.INFO)

        observer = LoggingObserver()
        observer.on_calculation(sample_calc)

        for h in logging.getLogger("calculator").handlers:
            h.flush()

        content = open(os.path.join(log_dir, log_file), encoding="utf-8").read()
        assert "INFO" in content


# ---------------------------------------------------------------------------
# REPL logging integration (via Calculator facade)
# ---------------------------------------------------------------------------


class TestREPLLogging:
    """Integration tests verifying that the REPL writes to the log file."""

    @pytest.fixture
    def calculator(self, tmp_path):
        from app.calculator_repl import Calculator
        env = tmp_path / ".env"
        env.write_text(
            f"CALCULATOR_LOG_DIR={tmp_path}/logs\n"
            f"CALCULATOR_HISTORY_DIR={tmp_path}/data\n"
            "CALCULATOR_LOG_FILE=repl_test.log\n"
            "CALCULATOR_AUTO_SAVE=false\n"
            "CALCULATOR_PRECISION=2\n"
        )
        return Calculator(env_path=str(env))

    def _read_log(self, tmp_path) -> str:
        log_path = tmp_path / "logs" / "repl_test.log"
        for handler in logging.getLogger("calculator").handlers:
            handler.flush()
        return log_path.read_text(encoding="utf-8") if log_path.exists() else ""

    def test_successful_calculation_logged_info(self, calculator, tmp_path) -> None:
        """Successful calculation produces an INFO log entry."""
        calculator.process_input("add 3 4")
        content = self._read_log(tmp_path)
        assert "INFO" in content
        assert "3 + 4 = 7.00" in content

    def test_failed_calculation_logged_error(self, calculator, tmp_path) -> None:
        """Division by zero produces an ERROR log entry."""
        calculator.process_input("divide 5 0")
        content = self._read_log(tmp_path)
        assert "ERROR" in content

    def test_invalid_input_logged_warning(self, calculator, tmp_path) -> None:
        """Non-numeric operand produces a WARNING log entry."""
        calculator.process_input("add abc 1")
        content = self._read_log(tmp_path)
        assert "WARNING" in content

    def test_undo_logged(self, calculator, tmp_path) -> None:
        """Undo operation produces an INFO log entry."""
        calculator.process_input("add 1 1")
        calculator.process_input("undo")
        content = self._read_log(tmp_path)
        assert "Undo" in content

    def test_save_logged(self, calculator, tmp_path) -> None:
        """Save command produces an INFO log entry."""
        calculator.process_input("add 2 2")
        calculator.process_input("save")
        content = self._read_log(tmp_path)
        assert "History manually saved" in content
