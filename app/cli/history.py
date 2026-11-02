"""
Calculation History and Observer Pattern
========================================

Manages the history of calculations using a pandas DataFrame and implements
the Observer design pattern.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal, InvalidOperation
import pandas as pd

from app.cli.calculation import Calculation
from app.core.logger import get_logger
from app.cli.command_loader import command_manager



class CalculationObserver(ABC):
    """Abstract base class for observers in the Observer design pattern."""

    @abstractmethod
    def on_calculation(self, calculation: Calculation) -> None:
        """Called when a new calculation is added to the history."""


class LoggingObserver(CalculationObserver):
    """An observer that logs each new calculation to the application's log file."""

    def __init__(self, **kwargs) -> None:
        self.logger = get_logger("history")

    def on_calculation(self, calculation: Calculation) -> None:
        self.logger.info("New calculation recorded: %s", calculation)


class AutoSaveObserver(CalculationObserver):
    """An observer that automatically saves the history to a CSV file."""

    def __init__(self, history: "CalculationHistory", enabled: bool = True) -> None:
        self._history = history
        self.enabled = enabled

    def on_calculation(self, calculation: Calculation) -> None:
        if self.enabled:
            self._history.save_to_csv()


class CalculationHistory:
    """
    Manages a history of calculations using a pandas DataFrame.

    Acts as the "Subject" in the Observer pattern. Handles persistence to/from CSV.
    """

    _COLUMNS = ["timestamp", "operand_a", "operand_b", "operation", "result"]

    def __init__(
        self,
        history_dir: str = "data",
        history_file: str = "history.csv",
        encoding: str = "utf-8",
        max_size: int = 1000,
    ) -> None:
        self.history_dir = history_dir
        self.history_file = history_file
        self.encoding = encoding
        self.max_size = max_size

        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)

        self.csv_path = os.path.join(self.history_dir, self.history_file)
        self._df = pd.DataFrame(columns=self._COLUMNS)
        self._observers: list[CalculationObserver] = []

    def add_observer(self, observer: CalculationObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: CalculationObserver) -> None:
        self._observers.remove(observer)

    def _notify_observers(self, calculation: Calculation) -> None:
        for observer in self._observers:
            observer.on_calculation(calculation)

    def add(self, calculation: Calculation) -> None:
        calc_dict = self._calculation_to_dict(calculation)
        self._df.loc[len(self._df)] = calc_dict
        if len(self._df) > self.max_size:
            self._df = self._df.tail(self.max_size).reset_index(drop=True)
        self._notify_observers(calculation)

    def get_all(self) -> list[dict]:
        return self._df.to_dict(orient="records")

    def get_calculations(self) -> list[Calculation]:
        calculations = []
        for index, row_dict in enumerate(self._df.to_dict(orient="records")):
            try:
                calc = self._dict_to_calculation(row_dict)
                if calc.result is None:
                    calc.execute()
                calculations.append(calc)
            except Exception as e:
                logging.warning(
                    "Skipping malformed history row #%d during load: %s | Error: %s",
                    index, row_dict, e,
                )
        return calculations

    def get_dataframe(self) -> pd.DataFrame:
        return self._df.copy()

    def set_dataframe(self, df: pd.DataFrame) -> None:
        self._df = df.copy()

    def clear(self) -> None:
        self._df = pd.DataFrame(columns=self._COLUMNS)

    def __len__(self) -> int:
        return len(self._df)

    def __repr__(self) -> str:
        return f"CalculationHistory({len(self._df)} calculations)"

    def save_to_csv(self, path: str | None = None) -> str:
        target_path = path or self.csv_path
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        self._df.to_csv(target_path, index=False, encoding=self.encoding)
        return target_path

    def load_from_csv(self, path: str | None = None) -> int:
        target_path = path or self.csv_path
        if not os.path.exists(target_path):
            return 0
        try:
            self._df = pd.read_csv(target_path, dtype=str).fillna("")
            self._df = self._df.reindex(columns=self._COLUMNS, fill_value="")
            if len(self._df) > self.max_size:
                self._df = self._df.tail(self.max_size).reset_index(drop=True)

            loaded_calculations = []
            for index, row_dict in enumerate(self._df.to_dict(orient="records")):
                try:
                    calc = self._dict_to_calculation(row_dict)
                    if calc.result is None:
                        calc.execute()
                    loaded_calculations.append(calc)
                except Exception as e:
                    logging.warning(
                        "Skipping malformed history row #%d during load: %s | Error: %s",
                        index, row_dict, e,
                    )

            self._df = pd.DataFrame(
                [self._calculation_to_dict(c) for c in loaded_calculations],
                columns=self._COLUMNS,
            )
            return len(self._df)
        except Exception:
            self.clear()
            return 0

    def _calculation_to_dict(self, calc: Calculation) -> dict:
        return {
            "timestamp": calc.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "operand_a": str(calc.operand_a),
            "operand_b": str(calc.operand_b),
            "operation": calc.operation_name,
            "result": str(calc.result) if calc.result is not None else "",
        }

    def _dict_to_calculation(self, row: dict) -> Calculation:
        command_name = row.get("operation")
        if not command_name:
            raise ValueError("Missing operation name in history row.")

        command = command_manager.get_command(command_name)
        if not command:
            raise ValueError(f"Unknown operation '{command_name}' in history.")

        operand_a_str = row.get("operand_a", "")
        operand_b_str = row.get("operand_b", "")

        try:
            operand_a = Decimal(operand_a_str) if operand_a_str else Decimal(0)
            operand_b = Decimal(operand_b_str) if operand_b_str else Decimal(0)
        except InvalidOperation as e:
            raise ValueError(f"Invalid numeric operand in history row: {e}") from e

        calc = Calculation(operand_a, operand_b, command.handler, command_name)

        result_str = row.get("result")
        if result_str and result_str != "None":
            try:
                calc.result = Decimal(result_str)
            except InvalidOperation as e:
                logging.warning("Invalid result format in history for row: %s. Error: %s", row, e)

        timestamp_str = row.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        try:
            calc.timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            logging.warning(
                "Invalid timestamp format in history for row: %s. Using current time. Error: %s",
                row, e,
            )
            calc.timestamp = datetime.now()

        return calc
