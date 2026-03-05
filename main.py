"""
Entry point for the Calculator application.

This module initializes and runs the calculator's Read-Eval-Print Loop (REPL).
It serves as the main entry point when the application is executed from the command line.
"""

from app.calculator_factory import CalculatorFactory


def main() -> None:
    """
    Create a Calculator instance and start the REPL.

    This function initializes the `Calculator` object, which encapsulates the
    application's core logic, and then calls its `run` method to start the
    interactive command-line interface.
    """
    calculator = CalculatorFactory.create_calculator()
    calculator.run()


if __name__ == "__main__":  # pragma: no cover
    # This block ensures that the main() function is called only when the script
    # is executed directly, not when it's imported as a module into another script.
    main()
