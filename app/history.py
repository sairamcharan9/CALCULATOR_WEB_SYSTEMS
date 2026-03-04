"""
Calculation History and Observer Pattern
========================================

This module is responsible for managing the history of calculations. It uses
a pandas DataFrame for efficient data storage and manipulation. The module also
implements the Observer design pattern, allowing other parts of the application
to be notified when the history changes.

Key Components:
    - `CalculationHistory`: The "Subject" that maintains the list of calculations
      and notifies observers of changes. It handles persistence to/from CSV.
    - `CalculationObserver`: An abstract base class defining the interface for
      all "Observers".
    - `LoggingObserver`: A concrete observer that logs new calculations.
    - `AutoSaveObserver`: A concrete observer that saves the history to a file
      after each new calculation.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal, InvalidOperation
import pandas as pd

from app.calculation import Calculation
from app.logger import get_logger
from app.command_loader import command_manager

class CalculationObserver(ABC):
    """
    Abstract base class for observers in the Observer design pattern.
    
    Observers are notified when a new calculation is added to the history.
    """

    @abstractmethod
    def on_calculation(self, calculation: Calculation) -> None:
        """
        This method is called by the `CalculationHistory` subject when a new
        calculation is added.

        Args:
            calculation (Calculation): The `Calculation` instance that was just added.
        """

class LoggingObserver(CalculationObserver):
    """
    An observer that logs each new calculation to the application's log file.
    
    This observer uses a specific logger (`calculator.history`) to route its
    messages through the centralized logging configuration.
    """

    def __init__(self, **kwargs) -> None:
        """Initializes the observer and gets a dedicated logger instance."""
        self.logger = get_logger("history")

    def on_calculation(self, calculation: Calculation) -> None:
        """Logs the details of a new calculation at the INFO level."""
        self.logger.info(
            "New calculation recorded: %s", calculation
        )

class AutoSaveObserver(CalculationObserver):
    """
    An observer that automatically saves the entire calculation history to a CSV
    file whenever a new calculation is added.
    
    This feature can be enabled or disabled via the `enabled` attribute.
    """

    def __init__(self, history: "CalculationHistory", enabled: bool = True) -> None:
        """
        Initializes the observer with a reference to the history and its enabled state.
        """
        self._history = history
        self.enabled = enabled

    def on_calculation(self, calculation: Calculation) -> None:
        """
        Saves the full history to its configured CSV file if auto-saving is enabled.
        """
        if self.enabled:
            self._history.save_to_csv()

class CalculationHistory:
    """
    Manages a history of calculations using a pandas DataFrame.
    
    This class acts as the "Subject" in the Observer pattern. It maintains a list
    of observers and notifies them whenever a new calculation is added. It also
    handles persistence, saving to and loading from a CSV file.

    Attributes:
        history_dir (str): Directory where the history file is stored.
        history_file (str): Name of the CSV file for persistence.
        encoding (str): The file encoding to use for CSV operations.
        max_size (int): The maximum number of history entries to maintain.
    """

    _COLUMNS = ["timestamp", "operand_a", "operand_b", "operation", "result"]

    def __init__(self, history_dir: str = "data", history_file: str = "history.csv", encoding: str = "utf-8", max_size: int = 1000) -> None:
        """
        Initializes the CalculationHistory instance.

        Args:
            history_dir (str): The directory for storing the history file.
            history_file (str): The name of the history file.
            encoding (str): The file encoding to use.
            max_size (int): The maximum number of records to keep in the history.
        """
        self.history_dir = history_dir
        self.history_file = history_file
        self.encoding = encoding
        self.max_size = max_size

        # Ensure the directory for storing history exists.
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)

        self.csv_path = os.path.join(self.history_dir, self.history_file)
        self._df = pd.DataFrame(columns=self._COLUMNS)
        self._observers: list[CalculationObserver] = []

    def add_observer(self, observer: CalculationObserver) -> None:
        """Registers an observer to be notified of new calculations."""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: CalculationObserver) -> None:
        """Unregisters an observer."""
        self._observers.remove(observer)

    def _notify_observers(self, calculation: Calculation) -> None:
        """Notifies all registered observers about a new calculation."""
        for observer in self._observers:
            observer.on_calculation(calculation)

    def add(self, calculation: Calculation) -> None:
        """
        Adds a new calculation to the history and notifies all observers.
        If the history exceeds `max_size`, the oldest entry is removed.

        Args:
            calculation (Calculation): The calculation to add to the history.
        """
        new_row = pd.DataFrame([self._calculation_to_dict(calculation)])
        self._df = pd.concat([self._df, new_row], ignore_index=True)

        # Enforce the maximum history size by keeping only the most recent entries.
        if len(self._df) > self.max_size:
            self._df = self._df.tail(self.max_size).reset_index(drop=True)

        # Notify all registered observers of the new calculation.
        self._notify_observers(calculation)

    def get_all(self) -> list[dict]:
        """Returns the entire calculation history as a list of dictionaries."""
        return self._df.to_dict(orient="records")

    def get_calculations(self) -> list[Calculation]:
        """
        Reconstructs and returns the history as a list of `Calculation` objects.
        Each calculation object will have its `result` property set if it was
        available in the history.
        """
        calculations = []
        for index, row in self._df.iterrows():
            try:
                calc = self._dict_to_calculation(row.to_dict())
                # Execute the calculation to ensure the result is computed, especially for old entries
                # where result might have been stored as None or empty string.
                if calc.result is None:
                    calc.execute() # Ensure result is set after loading
                calculations.append(calc)
            except Exception as e:
                logging.warning("Skipping malformed history row #%d during load: %s | Error: %s", index, row.to_dict(), e)
        return calculations

    def get_dataframe(self) -> pd.DataFrame:
        """Returns a copy of the internal history DataFrame."""
        return self._df.copy()

    def set_dataframe(self, df: pd.DataFrame) -> None:
        """Replaces the internal DataFrame, used for undo/redo."""
        self._df = df.copy()

    def clear(self) -> None:
        """Clears all entries from the history."""
        self._df = pd.DataFrame(columns=self._COLUMNS)

    def __len__(self) -> int:
        """Returns the number of calculations in the history."""
        return len(self._df)

    def __repr__(self) -> str:
        """Returns a string representation of the history object."""
        return f"CalculationHistory({len(self._df)} calculations)"

    def save_to_csv(self, path: str | None = None) -> str:
        """
        Saves the history to a CSV file.
        """
        target_path = path or self.csv_path
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        self._df.to_csv(target_path, index=False, encoding=self.encoding)
        return target_path

    def load_from_csv(self, path: str | None = None) -> int:
        """
        Loads history from a CSV, replacing current data. If a loaded calculation
        does not have a result (e.g., from an older history file), its execute()
        method will be called to compute it.
        """
        target_path = path or self.csv_path
        if not os.path.exists(target_path):
            return 0
        try:
            self._df = pd.read_csv(target_path, dtype=str).fillna("")
            # Ensure columns are in the correct order and exist
            self._df = self._df.reindex(columns=self._COLUMNS, fill_value="")
            if len(self._df) > self.max_size:
                self._df = self._df.tail(self.max_size).reset_index(drop=True)

            # Reconstruct and execute calculations to ensure results are set
            # This creates new Calculation objects, so we need to replace the dataframe.
            loaded_calculations = []
            for index, row in self._df.iterrows():
                try:
                    calc = self._dict_to_calculation(row.to_dict())
                    if calc.result is None:
                        calc.execute() # Ensure result is set after loading
                    loaded_calculations.append(calc)
                except Exception as e:
                    logging.warning("Skipping malformed history row #%d during load: %s | Error: %s", index, row.to_dict(), e)
            
            self._df = pd.DataFrame([self._calculation_to_dict(c) for c in loaded_calculations], columns=self._COLUMNS)

            return len(self._df)
        except Exception:
            # In case of a corrupted file, start with an empty history
            self.clear()
            return 0

    def _calculation_to_dict(self, calc: Calculation) -> dict:
        """
        Converts a Calculation object to a dictionary for DataFrame storage.
        Stores the result as a string, including "" if it hasn't been executed.
        """
        return {
            "timestamp": calc.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "operand_a": str(calc.operand_a),
            "operand_b": str(calc.operand_b),
            "operation": calc.operation_name,
            "result": str(calc.result) if calc.result is not None else "", # Store "" if not executed
        }

    def _dict_to_calculation(self, row: dict) -> Calculation:
        """
        Converts a dictionary (from a DataFrame row) back to a Calculation object.
        The result is set if available in the row, otherwise it remains None.
        """
        command_name = row.get("operation")
        if not command_name:
            raise ValueError("Missing operation name in history row.")

        command = command_manager.get_command(command_name)
        if not command:
            raise ValueError(f"Unknown operation '{command_name}' in history.")

        operand_a_str = row.get("operand_a", "")
        operand_b_str = row.get("operand_b", "")

        try:
            operand_a = Decimal(operand_a_str) if operand_a_str else Decimal(0) # Default to 0 if missing/empty
            operand_b = Decimal(operand_b_str) if operand_b_str else Decimal(0) # Default to 0 if missing/empty
        except InvalidOperation as e:
            raise ValueError(f"Invalid numeric operand in history row: {e}") from e

        calc = Calculation(operand_a, operand_b, command.handler, command_name,)
        
        result_str = row.get("result")
        if result_str and result_str != "None":
            try:
                calc.result = Decimal(result_str)
            except InvalidOperation as e:
                logging.warning(f"Invalid result format in history for row: {row}. Error: {e}")
                # calc.result remains None, will be re-executed if needed.

        timestamp_str = row.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        try:
            calc.timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            logging.warning(f"Invalid timestamp format in history for row: {row}. Using current time. Error: {e}")
            calc.timestamp = datetime.now() # Fallback to current time

        return calc
