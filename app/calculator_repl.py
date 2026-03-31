from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

import colorama
from colorama import Fore

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import MementoCaretaker
from app.command_loader import command_manager
from app.exceptions import CalculationError, DivisionByZeroError
from app.history import CalculationHistory
from app.input_validators import validate_input_parts

colorama.init(autoreset=True)


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

    def __init__(self) -> None:
        """
        Initializes the Calculator, but delegates complex setup to the factory.
        """
        self.config: CalculatorConfig | None = None
        self.history: CalculationHistory | None = None
        self.caretaker: MementoCaretaker | None = None
        self._log: logging.Logger | None = None

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
                if "<" in command_obj.usage and "[" not in command_obj.usage:
                    return self._handle_arithmetic_command(command_obj, parts)
                else:
                    # Pass 'self' (the calculator instance) to the command handler
                    return command_obj.handler(self, *parts[1:])
            except Exception as e:
                # Handle potential errors within the command handler
                self._log.error("Error executing command '%s': %s", command, e)
                print(f"Error: {e}")
                return str(e)

        # If not a registered command, check if it's explicitly "calc" for arithmetic operations
        if command == "calc":
            # "calc <operation> <n1> <n2>" needs at least 4 parts: "calc", operation, operand_a, operand_b
            if len(parts) < 4:
                msg = "Error: Usage for 'calc' is 'calc <operation> <n1> <n2>'."
                print(f"{Fore.RED}{msg}")
                self._log.warning(msg)
                return msg

            # The actual arithmetic operation is the second part (parts[1])
            arithmetic_operation_name = parts[1]
            arithmetic_command_obj = command_manager.get_command(arithmetic_operation_name)
            
            if arithmetic_command_obj and ("<" in arithmetic_command_obj.usage and "[" not in arithmetic_command_obj.usage):
                # Pass the actual operation and its operands (from parts[1] onwards)
                return self._handle_arithmetic_command(arithmetic_command_obj, parts[1:])
            else:
                msg = f"Error: '{arithmetic_operation_name}' is not a valid arithmetic operation for 'calc'."
                print(f"{Fore.RED}{msg}")
                self._log.warning(msg)
                return msg
        else:
            # If it's not a registered command and not "calc", it's an unknown command
            msg = f"Error: Unknown command '{command}'."
            self._log.warning(msg)
            print(f"{Fore.RED}{msg}")
            return msg

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
            calc.execute()  # Execute the calculation command
            self.caretaker.save()
            self.history.add(calc)
            result_msg = f"Result: {calc}"
            self._log.info("Calculation successful: %s -> %s", calc, calc.result)
            print(f"{Fore.GREEN}{result_msg}")
            return result_msg
        except InvalidOperation:
            msg = f"Error: Invalid number input. '{raw_a}' or '{raw_b}' is not a valid number."
            self._log.warning("Invalid number input: a='%s', b='%s'", raw_a, raw_b)
            print(f"{Fore.RED}{msg}")
            return msg
        except (CalculationError, DivisionByZeroError) as e:
            msg = f"Error: {e}"
            self._log.error("Calculation error for %s(%s, %s): %s", operation_name, operand_a, operand_b, e)
            print(f"{Fore.RED}{msg}")
            return msg

    @staticmethod
    def _print_welcome() -> None:  # pragma: no cover
        """Prints the welcome banner when the REPL starts."""
        print(
            f"{Fore.MAGENTA}================================\n"
            f"   Welcome to the Calculator!\n"
            f"================================\n"
            f"{Fore.CYAN}Type 'help' for available commands.\nType 'exit' to quit."
        )