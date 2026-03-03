"""
History Module (Observer Pattern + pandas)
===========================================

Manages calculation history using a pandas ``DataFrame`` and notifies
registered observers whenever a new calculation is added.

Key classes:
    - **CalculationObserver** (ABC): base for Observer pattern implementations.
    - **LoggingObserver**: prints a log line for each calculation.
    - **AutoSaveObserver**: automatically saves history to CSV on each add.
    - **CalculationHistory**: stores history in a ``DataFrame``, supports
      save / load to CSV, and observer notification.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from decimal import Decimal

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

    logger = logging.getLogger("calculator.history")

    def __init__(self) -> None:
        self.log_messages: list[str] = []

    def on_calculation(self, calculation: Calculation) -> None:
        """Log the calculation via the logging module and internal list."""
        msg = f"[LOG] {calculation}"
        self.log_messages.append(msg)
        self.logger.info("Calculation: %s", calculation)
        try:
            print(msg)
        except UnicodeEncodeError:
            print(msg.encode('ascii', errors='replace').decode('ascii'))


class AutoSaveObserver(CalculationObserver):
    """Observer that auto-saves the history to CSV on every calculation."""

    def __init__(self, history: "CalculationHistory") -> None:
        self._history = history

    def on_calculation(self, calculation: Calculation) -> None:  # pragma: no cover
        """Save the full history to the configured CSV file."""
        self._history.save_to_csv()


# ---------------------------------------------------------------------------
# CalculationHistory — pandas-backed
# ---------------------------------------------------------------------------


class CalculationHistory:
    """Stores calculation history as a pandas ``DataFrame``.

    Observers are notified whenever a calculation is added so they
    can react (e.g., logging, auto-saving).

    Attributes:
        csv_path: Path to the CSV file for persistence.
    """

    _COLUMNS = ["operand_a", "operand_b", "operation", "result"]

    def __init__(self, csv_path: str = "history.csv") -> None:
        """Initialize an empty history.

        Args:
            csv_path: File path used for ``save_to_csv`` / ``load_from_csv``.
        """
        self.csv_path = csv_path
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
                    "operand_a": str(calculation.operand_a),
                    "operand_b": str(calculation.operand_b),
                    "operation": calculation.operation_name,
                    "result": str(calculation.result),
                }
            ]
        )
        self._df = pd.concat([self._df, new_row], ignore_index=True)
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
        self._df.to_csv(target, index=False)
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
            self._df = pd.read_csv(target).fillna("")
            # Ensure expected columns exist
            for col in self._COLUMNS:
                if col not in self._df.columns:
                    self._df[col] = ""
            return len(self._df)
        return 0
