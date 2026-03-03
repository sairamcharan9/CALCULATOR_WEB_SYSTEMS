"""
History Module (Observer Pattern + pandas)
===========================================

Manages calculation history using a pandas ``DataFrame`` and notifies
registered observers whenever a new calculation is added.

Key classes:
    - **CalculationObserver** (ABC): base for Observer pattern implementations.
    - **LoggingObserver**: logs calculations to a file using the logging module.
    - **AutoSaveObserver**: automatically saves history to CSV on each add.
    - **CalculationHistory**: stores history in a ``DataFrame``, supports
      save / load to CSV, and observer notification.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from app.calculation import Calculation


# ---------------------------------------------------------------------------
# Observer base and concrete observers
# ---------------------------------------------------------------------------


class CalculationObserver(ABC):
    """Abstract base for observers reacting to new calculations."""

    @abstractmethod
    def on_calculation(self, calculation: Calculation) -> None:
        """Called when a new calculation is added to the history.

        Args:
            calculation: The newly added ``Calculation``.
        """


class LoggingObserver(CalculationObserver):
    """Observer that logs each new calculation using Python's logging module."""

    def __init__(self, log_dir: str = "logs", log_file: str = "calculator.log", encoding: str = "utf-8") -> None:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_path = os.path.join(log_dir, log_file)

        self.logger = logging.getLogger("calculator.history")
        self.logger.setLevel(logging.INFO)

        # Avoid adding multiple handlers if the observer is re-instantiated
        if not self.logger.handlers:
            handler = logging.FileHandler(log_path, encoding=encoding)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def on_calculation(self, calculation: Calculation) -> None:
        """Log the calculation via the logging module."""
        msg = f"Operation: {calculation.operation_name}, Operands: ({calculation.operand_a}, {calculation.operand_b}), Result: {calculation.result}"
        self.logger.info(msg)


class AutoSaveObserver(CalculationObserver):
    """Observer that auto-saves the history to CSV on every calculation."""

    def __init__(self, history: "CalculationHistory", enabled: bool = True) -> None:
        self._history = history
        self.enabled = enabled

    def on_calculation(self, calculation: Calculation) -> None:
        """Save the full history to the configured CSV file if enabled."""
        if self.enabled:
            self._history.save_to_csv()


# ---------------------------------------------------------------------------
# CalculationHistory — pandas-backed
# ---------------------------------------------------------------------------


class CalculationHistory:
    """Stores calculation history as a pandas ``DataFrame``.

    Observers are notified whenever a calculation is added so they
    can react (e.g., logging, auto-saving).

    Attributes:
        history_dir: Directory for history files.
        history_file: Name of the CSV file for persistence.
    """

    _COLUMNS = ["timestamp", "operand_a", "operand_b", "operation", "result"]

    def __init__(self, history_dir: str = "data", history_file: str = "history.csv", encoding: str = "utf-8", max_size: int = 1000) -> None:
        """Initialize an empty history.

        Args:
            history_dir: Directory for the CSV file.
            history_file: File name for persistence.
            encoding: Encoding for file operations.
            max_size: Maximum number of history entries.
        """
        self.history_dir = history_dir
        self.history_file = history_file
        self.encoding = encoding
        self.max_size = max_size

        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)

        self.csv_path = os.path.join(self.history_dir, self.history_file)
        self._df = pd.DataFrame(columns=self._COLUMNS)
        self._observers: list[CalculationObserver] = []

    # -- Observer management ------------------------------------------------

    def add_observer(self, observer: CalculationObserver) -> None:
        """Register an observer."""
        self._observers.append(observer)

    def remove_observer(self, observer: CalculationObserver) -> None:
        """Unregister an observer."""
        self._observers.remove(observer)

    def _notify_observers(self, calculation: Calculation) -> None:
        """Notify all registered observers about *calculation*."""
        for observer in self._observers:
            observer.on_calculation(calculation)

    # -- History operations -------------------------------------------------

    def add(self, calculation: Calculation) -> None:
        """Add a ``Calculation`` to the history and notify observers.

        Args:
            calculation: The calculation to record.
        """
        new_row = pd.DataFrame(
            [
                {
                    "timestamp": calculation.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "operand_a": str(calculation.operand_a),
                    "operand_b": str(calculation.operand_b),
                    "operation": calculation.operation_name,
                    "result": str(calculation.result),
                }
            ]
        )
        self._df = pd.concat([self._df, new_row], ignore_index=True)

        # Enforce max history size
        if len(self._df) > self.max_size:
            self._df = self._df.tail(self.max_size).reset_index(drop=True)

        self._notify_observers(calculation)

    def get_all(self) -> list[dict]:
        """Return all history rows as a list of dicts."""
        return self._df.to_dict(orient="records")

    def get_dataframe(self) -> pd.DataFrame:
        """Return a copy of the history ``DataFrame``."""
        return self._df.copy()

    def set_dataframe(self, df: pd.DataFrame) -> None:
        """Replace the history ``DataFrame`` (used by undo/redo)."""
        self._df = df.copy()

    def clear(self) -> None:
        """Remove all rows from the history."""
        self._df = pd.DataFrame(columns=self._COLUMNS)

    def __len__(self) -> int:
        """Return the number of rows in the history."""
        return len(self._df)

    def __repr__(self) -> str:
        return f"CalculationHistory({len(self._df)} calculations)"

    # -- Persistence --------------------------------------------------------

    def save_to_csv(self, path: str | None = None) -> str:
        """Save the history ``DataFrame`` to a CSV file.

        Args:
            path: Optional override for the file path.

        Returns:
            The path the file was written to.
        """
        target = path or self.csv_path
        target_dir = os.path.dirname(target)
        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir)
        self._df.to_csv(target, index=False, encoding=self.encoding)
        return target

    def load_from_csv(self, path: str | None = None) -> int:
        """Load history from a CSV file, replacing current contents.

        Args:
            path: Optional override for the file path.

        Returns:
            The number of rows loaded.
        """
        target = path or self.csv_path
        if os.path.exists(target):
            try:
                self._df = pd.read_csv(target, encoding=self.encoding).fillna("")
                # Ensure expected columns exist
                for col in self._COLUMNS:
                    if col not in self._df.columns:
                        self._df[col] = ""

                # Enforce max history size
                if len(self._df) > self.max_size:
                    self._df = self._df.tail(self.max_size).reset_index(drop=True)

                return len(self._df)
            except Exception as e:
                # Handle malformed CSV
                print(f"Error loading CSV: {e}")
                return 0
        return 0
