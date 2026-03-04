"""
Tests for the Calculation History Module
========================================

This module contains tests for the `CalculationHistory` and its related
observer classes. It covers basic history management (add, clear),
observer notifications, and CSV persistence.
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
import pandas as pd

from app import load_plugins
from app.calculation import Calculation
from app.history import (
    CalculationHistory,
    LoggingObserver,
    AutoSaveObserver,
)

load_plugins()

# Dummy calculation for testing
def dummy_op(a, b): return a + b

# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def history(tmp_path):
    """Provides a fresh CalculationHistory instance for each test."""
    return CalculationHistory(
        history_dir=str(tmp_path), history_file="test_hist.csv"
    )

@pytest.fixture
def sample_calc():
    """Provides a sample Calculation object for testing."""
    return Calculation(Decimal("2"), Decimal("3"), dummy_op, "add")

# ===========================================================================
# Test Cases
# ===========================================================================

class TestCalculationHistoryBasics:
    """Tests for core history management functions."""

    def test_empty_history(self, history: CalculationHistory):
        """History should be empty on initialization."""
        assert len(history) == 0
        assert history.get_all() == []

    def test_add_and_get_all(self, history: CalculationHistory, sample_calc: Calculation):
        """Test adding a calculation and retrieving the full history."""
        history.add(sample_calc)
        assert len(history) == 1
        
        # Verify the content of the history
        records = history.get_all()
        assert len(records) == 1
        assert records[0]["operation"] == "add"
        assert records[0]["operand_a"] == "2"

    def test_clear(self, history: CalculationHistory, sample_calc: Calculation):
        """Test that clear() removes all entries."""
        history.add(sample_calc)
        assert len(history) == 1
        
        history.clear()
        assert len(history) == 0

    def test_repr(self, history: CalculationHistory, sample_calc: Calculation):
        """Test the __repr__ method for a meaningful representation."""
        history.add(sample_calc)
        assert "1 calculations" in repr(history)

    def test_get_calculations(self, history: CalculationHistory, sample_calc: Calculation):
        """Test reconstructing Calculation objects from history."""
        history.add(sample_calc)
        calcs = history.get_calculations()
        assert len(calcs) == 1
        assert calcs[0].result == sample_calc.result

class TestObserverPattern:
    """Tests for the observer notification mechanism."""

    def test_add_and_notify_observer(self, history: CalculationHistory, sample_calc: Calculation):
        """Test that an observer is notified when a calculation is added."""
        # Create a mock observer
        observer = MagicMock()
        history.add_observer(observer)
        
        # Add a calculation, which should trigger notification
        history.add(sample_calc)
        
        # Verify that the observer's on_calculation method was called once
        observer.on_calculation.assert_called_once_with(sample_calc)

class TestLoggingObserver:
    """Tests for the logging observer."""

    @patch("app.history.get_logger")
    def test_logs_calculation(self, mock_get_logger, sample_calc: Calculation):
        """Test that the LoggingObserver logs the calculation."""
        # Mock the logger that the observer will use
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Create the observer and call its method
        observer = LoggingObserver()
        observer.on_calculation(sample_calc)
        
        # Check that the logger's info method was called
        mock_logger.info.assert_called_once()
        # Verify that the log message contains the string representation of the calculation
        args, _ = mock_logger.info.call_args
        assert args[1] == sample_calc

class TestCSVPersistence:
    """Tests for saving to and loading from CSV files."""

    def test_save_and_load(self, history: CalculationHistory, sample_calc: Calculation):
        """Test saving the history to a CSV and loading it back."""
        history.add(sample_calc)
        
        # Save to CSV
        save_path = history.save_to_csv()
        assert save_path.endswith("test_hist.csv")

        # Create a new history object and load from the saved file
        new_history = CalculationHistory(history_dir=history.history_dir, history_file="test_hist.csv")
        loaded_count = new_history.load_from_csv()
        
        assert loaded_count == 1
        assert len(new_history) == 1
        assert new_history.get_all()[0]["operation"] == "add"

    def test_load_nonexistent_file(self, history: CalculationHistory):
        """Loading a nonexistent file should result in an empty history."""
        count = history.load_from_csv("nonexistent_file.csv")
        assert count == 0
        assert len(history) == 0

    def test_auto_save_observer(self, history: CalculationHistory, sample_calc: Calculation):
        """Test that AutoSaveObserver saves history when a calculation is added."""
        # Spy on the save_to_csv method
        with patch.object(history, 'save_to_csv', MagicMock()) as mock_save:
            observer = AutoSaveObserver(history, enabled=True)
            history.add_observer(observer)
            
            history.add(sample_calc)
            
            # Verify that save was called
            mock_save.assert_called_once()

    def test_save_to_custom_path_creates_dirs(self, history: CalculationHistory, tmp_path):
        """Test that save_to_csv can create directories if they don't exist."""
        custom_path = tmp_path / "new_dir" / "custom_history.csv"
        history.save_to_csv(str(custom_path))
        assert custom_path.exists()

    def test_load_from_csv_exception_returns_zero(self, history, tmp_path):
        """If pd.read_csv fails, load_from_csv should return 0 and clear history."""
        path = tmp_path / "corrupted.csv"
        path.write_text("this is not a valid csv")
        
        count = history.load_from_csv(str(path))
        assert count == 0
        assert len(history) == 0

    def test_add_trims_to_max_size(self):
        """History should not grow beyond max_size."""
        history = CalculationHistory(max_size=2)
        history.add(Calculation(Decimal(1), Decimal(1), dummy_op, "add"))
        history.add(Calculation(Decimal(2), Decimal(2), dummy_op, "add"))
        history.add(Calculation(Decimal(3), Decimal(3), dummy_op, "add")) # This should push the first one out
        
        assert len(history) == 2
        records = history.get_all()
        assert records[0]['operand_a'] == '2' # The first one should be gone

    def test_load_from_csv_trims_to_max_size(self, tmp_path):
        """Loading a CSV larger than max_size should trim it."""
        path = tmp_path / "large.csv"
        df = pd.DataFrame({
            'timestamp': ['2023-01-01 12:00:00'] * 3,
            'operand_a': [1, 2, 3], 'operand_b': [1, 2, 3],
            'operation': ['add'] * 3, 'result': [2, 4, 6]
        })
        df.to_csv(path, index=False)
        
        history = CalculationHistory(history_dir=str(tmp_path), history_file="large.csv", max_size=2)
        count = history.load_from_csv()
        
        assert count == 2
        assert len(history) == 2

    def test_load_from_csv_with_missing_columns(self, tmp_path):
        """Loading a CSV with missing columns should fill them with empty strings."""
        path = tmp_path / "missing_cols.csv"
        df = pd.DataFrame({'operand_a': [1], 'operation': ['add']})
        df.to_csv(path, index=False)
        
        history = CalculationHistory(history_dir=str(tmp_path), history_file="missing_cols.csv")
        history.load_from_csv()
        
        record = history.get_all()[0]
        assert record['operand_b'] == ""
        assert record['result'] == ""

class TestObserverRemoval:
    def test_remove_observer_stops_notifications(self, history, sample_calc):
        """An observer should not be notified after it has been removed."""
        observer = MagicMock()
        history.add_observer(observer)
        history.remove_observer(observer)
        history.add(sample_calc)
        observer.on_calculation.assert_not_called()

class TestGetCalculations:
    def test_get_calculations_empty(self, history):
        """get_calculations should return an empty list for an empty history."""
        assert history.get_calculations() == []

    def test_get_calculations_multiple(self, history):
        """Test reconstructing multiple Calculation objects."""
        history.add(Calculation(Decimal("2"), Decimal("3"), dummy_op, "add"))
        history.add(Calculation(Decimal("10"), Decimal("4"), dummy_op, "subtract"))
        
        calcs = history.get_calculations()
        assert len(calcs) == 2
        assert calcs[0].operation_name == "add"
        assert calcs[1].operation_name == "subtract"

    def test_get_calculations_malformed_row_skipped(self, history, caplog):
        """A row that can't be converted to a Calculation should be skipped."""
        # Manually create a malformed DataFrame
        bad_df = pd.DataFrame([{"operation": "add", "operand_a": "two", "operand_b": "3"}])
        history.set_dataframe(bad_df)
        
        calcs = history.get_calculations()
        assert len(calcs) == 0
        assert "Skipping malformed history row" in caplog.text
