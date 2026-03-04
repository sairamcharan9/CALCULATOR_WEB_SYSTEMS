"""
Calculator REPL and Facade
==========================

This module provides the `Calculator` class, which serves as the main user-facing
interface for the application. It implements the Facade design pattern to simplify
the interaction with a complex subsystem of components.

The `Calculator` class coordinates:
- `CalculatorConfig` for settings management.
- `CalculationHistory` for tracking operations.
- `MementoCaretaker` for undo/redo functionality.
- Observers (`LoggingObserver`, `AutoSaveObserver`) for event handling.
- `input_validators` for command-line input validation.
- `CalculationFactory` for creating arithmetic calculations.
"""

from __future__ import annotations
import logging

from decimal import Decimal, InvalidOperation

from app.calculation import CalculationFactory
from app.calculator_config import CalculatorConfig
from app.calculator_memento import MementoCaretaker
from app.exceptions import (
    CalculationError,
    ConfigurationError,
)
from app.history import (
    AutoSaveObserver,
    CalculationHistory,
    LoggingObserver,
)
from app.input_validators import validate_input_parts
from app.logger import get_logger, reconfigure_logging


class Calculator:
    """
    An interactive calculator that provides a Read-Eval-Print Loop (REPL) interface.

    This class acts as a Facade, simplifying access to the calculator's
    subsystems, including configuration, history, memento for undo/redo,
    and calculation creation. It orchestrates the initialization and interaction
    of these components.

    Attributes:
        config (CalculatorConfig): The application's configuration settings.
        history (CalculationHistory): The manager for the calculation history.
        caretaker (MementoCaretaker): The manager for the undo/redo mementos.
    """

    SPECIAL_COMMANDS = ("help", "?", "history", "clear", "exit", "greet",
                        "undo", "redo", "save", "load",)

    def __init__(self, env_path: str | None = None) -> None:
        """
        Initializes all calculator subsystems in the correct order.

        Args:
            env_path (str | None): Optional path to a `.env` file for configuration.
        """
        # Step 1: Load Configuration
        # Tries to load from a .env file. If it fails due to invalid values,
        # it falls back to safe default settings to ensure the app can run.
        try:
            self.config = CalculatorConfig(env_path=env_path)
        except ConfigurationError:  # pragma: no cover
            self.config = CalculatorConfig()

        # Step 2: Set up Centralized Logging
        # This must be done early, as all other components use logging.
        reconfigure_logging(
            log_dir=self.config.log_dir,
            log_file=self.config.log_file,
            encoding=self.config.default_encoding,
        )
        self._log: logging.Logger = get_logger("repl")
        self._log.info("Calculator initializing with config: %s", self.config)

        # Step 3: Initialize Calculation History
        self.history = CalculationHistory(
            history_dir=self.config.history_dir,
            history_file=self.config.history_file,
            encoding=self.config.default_encoding,
            max_size=self.config.max_history_size
        )

        # Step 4: Set up Observers
        # Observers for logging and auto-saving are attached to the history.
        self.logging_observer = LoggingObserver(
            log_dir=self.config.log_dir,
            log_file=self.config.log_file,
            encoding=self.config.default_encoding
        )
        self.history.add_observer(self.logging_observer)
        self.auto_save_observer = AutoSaveObserver(self.history, enabled=self.config.auto_save)
        self.history.add_observer(self.auto_save_observer)

        # Step 5: Initialize Memento Caretaker for Undo/Redo
        self.caretaker = MementoCaretaker(self.history)

        # Step 6: Automatically Load Existing History from CSV
        loaded_count = self.history.load_from_csv()
        if loaded_count > 0:
            self._log.info("Auto-loaded %d calculation(s) from history CSV.", loaded_count)

    def run(self) -> None:  # pragma: no cover
        """Starts the Read-Eval-Print Loop (REPL) for user interaction."""
        self._print_welcome()
        while True:
            try:
                user_input = input("\n>>> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.lower() == "exit":
                print("Goodbye!")
                break

            self.process_input(user_input)

    def process_input(self, user_input: str) -> str:
        """
        Parses and executes a single line of user input.

        This method is the core of the REPL logic. It distinguishes between special
        commands (e.g., 'help') and arithmetic calculations. It uses a combination of
        LBYL (Look Before You Leap) for input validation and EAFP (Easier to Ask
        for Forgiveness than Permission) for handling calculation errors.

        Args:
            user_input (str): The raw string command entered by the user.

        Returns:
            str: A message indicating the result or status of the command.
        """
        parts = user_input.strip().lower().split()
        if not parts:
            return ""

        command = parts[0]
        self._log.debug("Processing user input: command='%s', parts=%s", command, parts)

        # Route to the appropriate handler based on the command.
        if command in ("help", "?"): return self._handle_help()
        if command == "history": return self._handle_history()
        if command == "clear": return self._handle_clear()
        if command == "undo": return self._handle_undo()
        if command == "redo": return self._handle_redo()
        if command == "save": return self._handle_save()
        if command == "load": return self._handle_load()
        if command == "greet": return self._handle_greet()

        # LBYL: Validate the format for an arithmetic operation.
        validation_error = validate_input_parts(parts, self.config.max_input_value)
        if validation_error:
            self._log.warning("Invalid input: %s (raw: '%s')", validation_error, user_input)
            print(validation_error)
            return validation_error

        operation_name, raw_a, raw_b = parts[0], parts[1], parts[2]

        # EAFP: Try to perform the calculation, catching potential errors.
        try:
            operand_a, operand_b = Decimal(raw_a), Decimal(raw_b)
            calc = CalculationFactory.create(operand_a, operand_b, operation_name, self.config.precision)
        except InvalidOperation:
            msg = f"Error: Invalid number input. '{raw_a}' or '{raw_b}' is not a valid number."
            self._log.warning("Invalid number input: a='%s', b='%s'", raw_a, raw_b)
            print(msg)
            return msg
        except CalculationError as e:
            msg = f"Error: {e}"
            self._log.error("Calculation error for %s(%s, %s): %s", operation_name, operand_a, operand_b, e)
            print(msg)
            return msg

        # After a successful calculation, save state and update history.
        self.caretaker.save()
        self.history.add(calc)
        result_msg = f"Result: {calc}"
        self._log.info("Calculation successful: %s -> %s", calc, calc.result)
        print(result_msg)
        return result_msg

    def _handle_help(self) -> str:
        """Displays a detailed help message with available operations and commands."""
        operations = ", ".join(CalculationFactory.get_supported_operations())
        help_text = (
            "=== Calculator Help ===\n\n"
            "Usage: <operation> <number1> <number2>\n\n"
            f"Available Operations: {operations}\n\n"
            "Examples:\n"
            "  add 10 5       -> 15.00\n"
            "  power 2 8      -> 256.00\n\n"
            "Special Commands:\n"
            "  help, ?    - Show this help message\n"
            "  history    - Show calculation history\n"
            "  clear      - Clear the history\n"
            "  undo/redo  - Undo or redo the last action\n"
            "  save/load  - Manually save or load history\n"
            "  exit       - Exit the application"
        )
        print(help_text)
        return help_text

    def _handle_history(self) -> str:
        """Displays the formatted calculation history."""
        rows = self.history.get_all()
        if not rows:
            msg = "No calculations in history."
            print(msg)
            return msg

        lines = ["=== Calculation History ==="]
        for i, row in enumerate(rows, start=1):
            lines.append(f"  {i}. {row['operand_a']} {row['operation']} {row['operand_b']} = {row['result']}")
        lines.append(f"\nTotal: {len(rows)} calculation(s)")
        history_text = "\n".join(lines)
        print(history_text)
        return history_text

    def _handle_clear(self) -> str:
        """Clears the calculation history, with undo support."""
        if len(self.history) == 0:
            msg = "History is already empty."
            print(msg)
            return msg
        
        self.caretaker.save()
        self.history.clear()
        msg = "History cleared."
        self._log.info("History cleared.")
        print(msg)
        return msg

    def _handle_undo(self) -> str:
        """Undoes the last action by restoring the previous history state."""
        if self.caretaker.undo():
            msg = f"Undo successful. History now contains {len(self.history)} calculation(s)."
            self._log.info("Undo successful. History size: %d", len(self.history))
        else:
            msg = "Nothing to undo."
            self._log.info("Undo requested, but undo stack is empty.")
        print(msg)
        return msg

    def _handle_redo(self) -> str:
        """Redoes the last undone action by restoring the next history state."""
        if self.caretaker.redo():
            msg = f"Redo successful. History now contains {len(self.history)} calculation(s)."
            self._log.info("Redo successful. History size: %d", len(self.history))
        else:
            msg = "Nothing to redo."
            self._log.info("Redo requested, but redo stack is empty.")
        print(msg)
        return msg

    def _handle_save(self) -> str:
        """Manually saves the current calculation history to a CSV file."""
        path = self.history.save_to_csv()
        msg = f"History saved to '{path}'."
        self._log.info("History manually saved to %s (%d rows)", path, len(self.history))
        print(msg)
        return msg

    def _handle_load(self) -> str:
        """Manually loads calculation history from a CSV file."""
        count = self.history.load_from_csv()
        msg = f"Loaded {count} calculation(s) from '{self.history.csv_path}'."
        self._log.info("History loaded from %s, containing %d rows", self.history.csv_path, count)
        print(msg)
        return msg

    def _handle_greet(self) -> str:
        """Displays a simple greeting message."""
        msg = "Hello! Welcome to the calculator."
        self._log.info("Displayed greeting message.")
        print(msg)
        return msg

    @staticmethod
    def _print_welcome() -> None:  # pragma: no cover
        """Prints the welcome banner when the REPL starts."""
        print(
            "================================\n"
            "   Welcome to the Calculator!\n"
            "================================\n"
            "Type 'help' for available commands.\n"
            "Type 'exit' to quit."
        )
