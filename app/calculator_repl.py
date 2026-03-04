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
from app.calculation import Calculation, CalculationFactory
import colorama
from colorama import Fore

colorama.init(autoreset=True)
from app.calculator_config import CalculatorConfig
from app.calculator_memento import MementoCaretaker
from app.command_loader import command_manager
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
                print(f"{Fore.YELLOW}\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.lower() == "exit":
                print(f"{Fore.YELLOW}Goodbye!")
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

        # Look up the command in the CommandManager
        command_obj = command_manager.get_command(command)

        if command_obj:
            # If it's a registered command, execute its handler
            try:
                # Check if the command is an arithmetic command
                if "<" in command_obj.usage:
                    return self._handle_arithmetic_command(command_obj, parts)
                else:
                    # Pass 'self' (the calculator instance) to the command handler
                    return command_obj.handler(self, *parts[1:])
            except Exception as e:
                # Handle potential errors within the command handler
                self._log.error("Error executing command '%s': %s", command, e)
                print(f"Error: {e}")
                return str(e)

        validation_error = validate_input_parts(parts, self.config.max_input_value)
        if validation_error:
            self._log.warning("Invalid input: %s (raw: '%s')", validation_error, user_input)
            print(f"{Fore.RED}{validation_error}")
            return validation_error

    def _handle_arithmetic_command(self, command_obj, parts):
        """Handles the execution of arithmetic commands."""
        if len(parts) != 3:
            msg = f"Error: Invalid number of arguments for {parts[0]}. Usage: {command_obj.usage}"
            print(f"{Fore.RED}{msg}")
            return msg

        operation_name, raw_a, raw_b = parts[0], parts[1], parts[2]

        # EAFP: Try to perform the calculation, catching potential errors.
        try:
            operand_a, operand_b = Decimal(raw_a), Decimal(raw_b)
            # The command handler for arithmetic operations is the operation function itself
            calc = Calculation(operand_a, operand_b, command_obj.handler, operation_name, self.config.precision)
        except InvalidOperation:
            msg = f"Error: Invalid number input. '{raw_a}' or '{raw_b}' is not a valid number."
            self._log.warning("Invalid number input: a='%s', b='%s'", raw_a, raw_b)
            print(f"{Fore.RED}{msg}")
            return msg
        except CalculationError as e:
            msg = f"Error: {e}"
            self._log.error("Calculation error for %s(%s, %s): %s", operation_name, operand_a, operand_b, e)
            print(f"{Fore.RED}{msg}")
            return msg

        # After a successful calculation, save state and update history.
        self.caretaker.save()
        self.history.add(calc)
        result_msg = f"Result: {calc}"
        self._log.info("Calculation successful: %s -> %s", calc, calc.result)
        print(f"{Fore.GREEN}{result_msg}")
        return result_msg

    @staticmethod
    def _print_welcome() -> None:  # pragma: no cover
        """Prints the welcome banner when the REPL starts."""
        print(
            f"{Fore.MAGENTA}================================\n"
            f"   Welcome to the Calculator!\n"
            f"================================\n"
            f"{Fore.CYAN}Type 'help' for available commands.\n"
            f"Type 'exit' to quit."
        )
