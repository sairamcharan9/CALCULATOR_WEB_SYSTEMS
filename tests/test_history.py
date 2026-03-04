"""
Tests for the History Module
==============================

Tests for CalculationHistory (pandas-backed), observer notifications,
LoggingObserver, CSV save/load, and DataFrame get/set.
"""

import os
import pytest
import pandas as pd
from decimal import Decimal
from unittest.mock import MagicMock
import logging

from app.calculation import Calculation
from app.operations import add, subtract
from app.history import (
    CalculationHistory,
    CalculationObserver,
    LoggingObserver,
    AutoSaveObserver,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def history_setup(tmp_path):
    """Provide a fresh CalculationHistory using a temp CSV path."""
    history_dir = str(tmp_path / "data")
    log_dir = str(tmp_path / "logs")
    return history_dir, log_dir


@pytest.fixture
def history(history_setup) -> CalculationHistory:
    history_dir, _ = history_setup
    return CalculationHistory(history_dir=history_dir, history_file="test_history.csv")


@pytest.fixture
def sample_calc() -> Calculation:
    """Provide a sample add calculation."""
    return Calculation(Decimal("2"), Decimal("3"), add, "add", precision=2)


# ---------------------------------------------------------------------------
# CalculationHistory basic operations
# ---------------------------------------------------------------------------


class TestCalculationHistoryBasics:
    """Test add, get_all, clear, len, repr."""

    def test_empty_history(self, history: CalculationHistory) -> None:
        """New history is empty."""
        assert len(history) == 0
        assert history.get_all() == []

    def test_add_and_get_all(
        self, history: CalculationHistory, sample_calc: Calculation
    ) -> None:
        """Adding a calculation appears in get_all."""
        history.add(sample_calc)
        rows = history.get_all()
        assert len(rows) == 1
        assert rows[0]["operation"] == "add"
        assert "timestamp" in rows[0]

    def test_clear(
        self, history: CalculationHistory, sample_calc: Calculation
    ) -> None:
        """Clearing removes all rows."""
        history.add(sample_calc)
        history.clear()
        assert len(history) == 0

    def test_repr(self, history: CalculationHistory) -> None:
        """Repr shows count."""
        assert "0 calculations" in repr(history)

    def test_get_calculations(self, history: CalculationHistory, sample_calc: Calculation) -> None:
        """get_calculations returns Calculation instances."""
        history.add(sample_calc)
        calcs = history.get_calculations()
        assert len(calcs) == 1
        assert isinstance(calcs[0], Calculation)
        assert calcs[0].result == sample_calc.result


# ---------------------------------------------------------------------------
# Observer pattern
# ---------------------------------------------------------------------------


class TestObserverPattern:
    """Test observer registration and notification."""

    def test_add_and_notify_observer(
        self, history: CalculationHistory, sample_calc: Calculation
    ) -> None:
        """Observer's on_calculation is called when a calc is added."""
        mock_observer = MagicMock(spec=CalculationObserver)
        history.add_observer(mock_observer)
        history.add(sample_calc)
        mock_observer.on_calculation.assert_called_once_with(sample_calc)


# ---------------------------------------------------------------------------
# LoggingObserver
# ---------------------------------------------------------------------------


class TestLoggingObserver:
    """Tests for LoggingObserver."""

    def test_logs_calculation(self, sample_calc: Calculation, history_setup) -> None:
        """Calculation is logged to file."""
        _, log_dir = history_setup
        log_file = "test_calc.log"
        observer = LoggingObserver(log_dir=log_dir, log_file=log_file)

        # We might need to handle the singleton logger in tests
        with MagicMock() as mock_logger:
            observer.logger = mock_logger
            observer.on_calculation(sample_calc)
            mock_logger.info.assert_called_once()


# ---------------------------------------------------------------------------
# CSV persistence
# ---------------------------------------------------------------------------


class TestCSVPersistence:
    """Tests for save_to_csv and load_from_csv."""

    def test_save_and_load(
        self, history: CalculationHistory, sample_calc: Calculation
    ) -> None:
        """Saving and loading preserves data."""
        history.add(sample_calc)
        history.save_to_csv()

        new_history = CalculationHistory(history_dir=history.history_dir, history_file=history.history_file)
        count = new_history.load_from_csv()
        assert count == 1
        assert len(new_history) == 1

    def test_load_nonexistent_file(self, history: CalculationHistory) -> None:
        """Loading from a nonexistent file returns 0."""
        count = history.load_from_csv("/nonexistent/path.csv")
        assert count == 0

    def test_auto_save_observer(self, history: CalculationHistory, sample_calc: Calculation):
        observer = AutoSaveObserver(history, enabled=True)
        history.add_observer(observer)
        history.add(sample_calc)
        assert os.path.exists(history.csv_path)

    def test_save_to_custom_path_creates_dirs(self, history: CalculationHistory, sample_calc: Calculation, tmp_path) -> None:
        """save_to_csv creates intermediate directories when they don't exist."""
        custom_path = str(tmp_path / "deep" / "nested" / "history.csv")
        history.add(sample_calc)
        returned = history.save_to_csv(path=custom_path)
        assert returned == custom_path
        assert os.path.exists(custom_path)

    def test_load_from_csv_exception_returns_zero(self, history: CalculationHistory, tmp_path) -> None:
        """load_from_csv returns 0 and does not raise if reading fails."""
        from unittest.mock import patch
        bad_path = str(tmp_path / "trigger_exc.csv")
        with open(bad_path, "w") as f:
            f.write("timestamp,operand_a,operand_b,operation,result\n")
        with patch("pandas.read_csv", side_effect=ValueError("Simulated read error")):
            count = history.load_from_csv(path=bad_path)
        assert count == 0

    def test_add_trims_to_max_size(self, tmp_path) -> None:
        """add() trims history to max_size when it exceeds the limit."""
        history = CalculationHistory(history_dir=str(tmp_path / "data"), history_file="h.csv", max_size=2)
        calcs = [
            Calculation(Decimal(str(i)), Decimal("1"), add, "add", precision=2)
            for i in range(4)
        ]
        for c in calcs:
            history.add(c)
        assert len(history) == 2

    def test_load_from_csv_trims_to_max_size(self, tmp_path) -> None:
        """load_from_csv enforces max_size on load."""
        history = CalculationHistory(history_dir=str(tmp_path / "data"), history_file="h.csv", max_size=2)
        rows = [{"timestamp": "2024-01-01 00:00:00", "operand_a": str(i), "operand_b": "1", "operation": "add", "result": str(i + 1)} for i in range(5)]
        csv_path = str(tmp_path / "data" / "h.csv")
        os.makedirs(str(tmp_path / "data"), exist_ok=True)
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        count = history.load_from_csv()
        assert count == 2
        assert len(history) == 2

    def test_load_from_csv_with_missing_columns(self, history: CalculationHistory, tmp_path) -> None:
        """Loading a CSV that is missing some expected columns fills them with empty string."""
        csv_path = str(tmp_path / "partial.csv")
        pd.DataFrame([{"timestamp": "2024-01-01 00:00:00", "operand_a": "1", "operand_b": "2", "operation": "add"}]).to_csv(csv_path, index=False)
        count = history.load_from_csv(path=csv_path)
        assert count == 1
        rows = history.get_all()
        assert "result" in rows[0]


# ---------------------------------------------------------------------------
# Observer pattern — remove_observer
# ---------------------------------------------------------------------------


class TestObserverRemoval:
    """Tests for remove_observer."""

    def test_remove_observer_stops_notifications(self, history: CalculationHistory, sample_calc: Calculation) -> None:
        """Removed observer is no longer called on new calculations."""
        mock_observer = MagicMock(spec=CalculationObserver)
        history.add_observer(mock_observer)
        history.add(sample_calc)
        assert mock_observer.on_calculation.call_count == 1

        history.remove_observer(mock_observer)
        history.add(sample_calc)
        assert mock_observer.on_calculation.call_count == 1


# ---------------------------------------------------------------------------
# get_calculations
# ---------------------------------------------------------------------------


class TestGetCalculations:
    """Tests for CalculationHistory.get_calculations()."""

    def test_get_calculations_empty(self, history: CalculationHistory) -> None:
        """Empty history returns empty list."""
        assert history.get_calculations() == []

    def test_get_calculations_multiple(self, history: CalculationHistory) -> None:
        """get_calculations returns all stored rows as Calculation objects."""
        calc1 = Calculation(Decimal("2"), Decimal("3"), add, "add", precision=2)
        calc2 = Calculation(Decimal("10"), Decimal("4"), subtract, "subtract", precision=2)
        history.add(calc1)
        history.add(calc2)
        calcs = history.get_calculations()
        assert len(calcs) == 2
        assert calcs[0].operation_name == "add"
        assert calcs[1].operation_name == "subtract"

    def test_get_calculations_malformed_row_skipped(self, history: CalculationHistory) -> None:
        """Rows with invalid data are skipped without raising."""
        bad_row = pd.DataFrame([{
            "timestamp": "2024-01-01 00:00:00",
            "operand_a": "not_a_number",
            "operand_b": "1",
            "operation": "unknown_op",
            "result": "42",
        }])
        history._df = pd.concat([history._df, bad_row], ignore_index=True)
        calcs = history.get_calculations()
        assert calcs == []
