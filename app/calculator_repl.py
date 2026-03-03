"""
Calculator REPL Module (Facade Pattern)
========================================

Provides the ``Calculator`` class — the primary user-facing interface
that acts as a **Facade** over:

- Configuration (``CalculatorConfig``)
- History management (``CalculationHistory``)
- Undo / Redo (``MementoCaretaker``)
- Observer notifications (``LoggingObserver``, ``AutoSaveObserver``)
- Input validation (``input_validators``)
- Arithmetic operations (``CalculationFactory``)

Commands:
    help, history, exit, clear, undo, redo, save, load
"""

from __future__ import annotations

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


class Calculator:
    """Interactive calculator with a REPL interface (Facade Pattern).

    Wraps configuration, history, memento, observers, validators,
    and the calculation factory behind a single easy-to-use class.

    Attributes:
        config: The ``CalculatorConfig`` instance.
        history: The ``CalculationHistory`` instance.
        caretaker: The ``MementoCaretaker`` for undo / redo.
    """

    SPECIAL_COMMANDS = ("help", "?", "history", "clear", "exit",
                        "undo", "redo", "save", "load")

    def __init__(self, env_path: str | None = None) -> None:
        """Initialize the calculator subsystems.

        Args:
            env_path: Optional path to a ``.env`` file.
        """
        # -- Configuration --------------------------------------------------
        try:
            self.config = CalculatorConfig(env_path=env_path)
        except ConfigurationError:  # pragma: no cover
            # Fall back to safe defaults if config is broken
            self.config = CalculatorConfig() # Will use defaults if .env is missing or broken

        # -- History (pandas) -----------------------------------------------
        self.history = CalculationHistory(
            history_dir=self.config.history_dir,
            history_file=self.config.history_file,
            encoding=self.config.default_encoding,
            max_size=self.config.max_history_size
        )

        # -- Observers ------------------------------------------------------
        self.logging_observer = LoggingObserver(
            log_dir=self.config.log_dir,
            log_file=self.config.log_file,
            encoding=self.config.default_encoding
        )
        self.history.add_observer(self.logging_observer)

        self.auto_save_observer = AutoSaveObserver(self.history, enabled=self.config.auto_save)
        self.history.add_observer(self.auto_save_observer)

        # -- Memento (undo / redo) ------------------------------------------
        self.caretaker = MementoCaretaker(self.history)

        # -- Auto-load existing history -------------------------------------
        self.history.load_from_csv()

    # ------------------------------------------------------------------
    # REPL
    # ------------------------------------------------------------------

    def run(self) -> None:  # pragma: no cover
        """Start the Read-Eval-Print Loop."""
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

    # ------------------------------------------------------------------
    # Input processing (public for testability)
    # ------------------------------------------------------------------

    def process_input(self, user_input: str) -> str:
        """Parse and execute a single line of user input.

        Uses **LBYL** to validate input format and **EAFP** to handle
        runtime errors (invalid numbers, division by zero).

        Args:
            user_input: The raw string entered by the user.

        Returns:
            A feedback message string.
        """
        parts = user_input.strip().lower().split()
        if not parts:
            return ""

        command = parts[0]

        # --- Handle special commands ---
        if command in ("help", "?"):
            return self._handle_help()
        if command == "history":
            return self._handle_history()
        if command == "clear":
            return self._handle_clear()
        if command == "undo":
            return self._handle_undo()
        if command == "redo":
            return self._handle_redo()
        if command == "save":
            return self._handle_save()
        if command == "load":
            return self._handle_load()

        # --- LBYL: validate format ---
        validation_error = validate_input_parts(parts, self.config.max_input_value)
        if validation_error:
            print(validation_error)
            return validation_error

        operation_name = parts[0]
        raw_a = parts[1]
        raw_b = parts[2]

        # --- EAFP: attempt numeric conversion and calculation ---
        try:
            operand_a = Decimal(raw_a)
            operand_b = Decimal(raw_b)
        except InvalidOperation:
            msg = (
                f"Error: '{raw_a}' and/or '{raw_b}' are not valid numbers. "
                "Please enter numeric values."
            )
            print(msg)
            return msg

        try:
            # Save state before mutation (for undo)
            self.caretaker.save()
            calc = CalculationFactory.create(operand_a, operand_b, operation_name, self.config.precision)
        except CalculationError as exc:
            msg = f"Error: {exc}"
            print(msg)
            return msg

        self.history.add(calc)
        result_msg = f"Result: {calc}"
        print(result_msg)
        return result_msg

    # ------------------------------------------------------------------
    # Special command handlers
    # ------------------------------------------------------------------

    def _handle_help(self) -> str:
        """Display help information."""
        operations = CalculationFactory.get_supported_operations()
        help_text = (
            "=== Calculator Help ===\n"
            "\n"
            "Usage: <operation> <number1> <number2>\n"
            "\n"
            f"Operations: {', '.join(operations)}\n"
            "\n"
            "Examples:\n"
            "  add 5 3        => 5 + 3 = 8.00\n"
            "  subtract 10 4  => 10 - 4 = 6.00\n"
            "  multiply 6 7   => 6 * 7 = 42.00\n"
            "  divide 20 4    => 20 / 4 = 5.00\n"
            "  power 2 8      => 2 ^ 8 = 256.00\n"
            "  root 9 2       => 9 √ 2 = 3.00\n"
            "  modulus 10 3   => 10 % 3 = 1.00\n"
            "  int_divide 10 3 => 10 // 3 = 3.00\n"
            "  percent 5 100  => 5 %% 100 = 5.00\n"
            "  abs_diff 5 10  => 5 |-| 10 = 5.00\n"
            "\n"
            "Special commands:\n"
            "  help / ?   - Show this help message\n"
            "  history    - Show calculation history\n"
            "  clear      - Clear calculation history\n"
            "  undo       - Undo last action\n"
            "  redo       - Redo last undone action\n"
            "  save       - Save history to CSV\n"
            "  load       - Load history from CSV\n"
            "  exit       - Exit the calculator"
        )
        print(help_text)
        return help_text

    def _handle_history(self) -> str:
        """Display the calculation history."""
        rows = self.history.get_all()
        if not rows:
            msg = "No calculations in history."
            print(msg)
            return msg

        lines = ["=== Calculation History ==="]
        for i, row in enumerate(rows, start=1):
            lines.append(
                f"  {i}. [{row['timestamp']}] {row['operand_a']} {row['operation']} "
                f"{row['operand_b']} = {row['result']}"
            )
        lines.append(f"\nTotal: {len(rows)} calculation(s)")
        history_text = "\n".join(lines)
        print(history_text)
        return history_text

    def _handle_clear(self) -> str:
        """Clear the calculation history."""
        self.caretaker.save()
        self.history.clear()
        msg = "History cleared."
        print(msg)
        return msg

    def _handle_undo(self) -> str:
        """Undo the last action."""
        if self.caretaker.undo():
            msg = "Undo successful."
        else:
            msg = "Nothing to undo."
        print(msg)
        return msg

    def _handle_redo(self) -> str:
        """Redo the last undone action."""
        if self.caretaker.redo():
            msg = "Redo successful."
        else:
            msg = "Nothing to redo."
        print(msg)
        return msg

    def _handle_save(self) -> str:
        """Save history to CSV."""
        path = self.history.save_to_csv()
        msg = f"History saved to '{path}'."
        print(msg)
        return msg

    def _handle_load(self) -> str:
        """Load history from CSV."""
        count = self.history.load_from_csv()
        msg = f"Loaded {count} calculation(s) from '{self.history.csv_path}'."
        print(msg)
        return msg

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _print_welcome() -> None:  # pragma: no cover
        """Print the welcome banner."""
        print(
            "================================\n"
            "   Welcome to the Calculator!\n"
            "================================\n"
            "Type 'help' for available commands.\n"
            "Type 'exit' to quit."
        )
