from __future__ import annotations
import logging

from app.calculator_config import CalculatorConfig
from app.calculator_memento import MementoCaretaker
from app.calculator_repl import Calculator
from app.exceptions import ConfigurationError
from app.history import (
    AutoSaveObserver,
    CalculationHistory,
    LoggingObserver,
)
from app.logger import get_logger, reconfigure_logging

class CalculatorFactory:
    """A factory for creating and configuring Calculator instances."""

    @staticmethod
    def create_calculator(env_path: str | None = None) -> Calculator:
        """
        Creates and configures a Calculator instance and its dependencies.

        Args:
            env_path (str | None): Optional path to a `.env` file for configuration.

        Returns:
            Calculator: A fully configured Calculator instance.
        """
        # Step 1: Load Configuration
        try:
            config = CalculatorConfig(env_path=env_path)
        except ConfigurationError:  # pragma: no cover
            config = CalculatorConfig()

        # Step 2: Set up Centralized Logging
        reconfigure_logging(
            log_dir=config.log_dir,
            log_file=config.log_file,
            encoding=config.default_encoding,
        )
        logger: logging.Logger = get_logger("factory")
        logger.info("Calculator initializing with config: %s", config)

        # Step 3: Initialize Calculation History
        history = CalculationHistory(
            history_dir=config.history_dir,
            history_file=config.history_file,
            encoding=config.default_encoding,
            max_size=config.max_history_size
        )

        # Step 4: Set up Observers
        logging_observer = LoggingObserver(
            log_dir=config.log_dir,
            log_file=config.log_file,
            encoding=config.default_encoding
        )
        history.add_observer(logging_observer)
        auto_save_observer = AutoSaveObserver(history, enabled=config.auto_save)
        history.add_observer(auto_save_observer)

        # Step 5: Initialize Memento Caretaker
        caretaker = MementoCaretaker(history)

        # Step 6: Load History
        loaded_count = history.load_from_csv()
        if loaded_count > 0:
            logger.info("Auto-loaded %d calculation(s) from history CSV.", loaded_count)

        # Step 7: Create Calculator instance
        calculator = Calculator()
        calculator.config = config
        calculator.history = history
        calculator.caretaker = caretaker
        calculator._log = get_logger("repl")
        
        return calculator
