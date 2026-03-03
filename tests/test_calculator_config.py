"""
Tests for the Calculator Config Module
========================================

Tests for CalculatorConfig: loading from .env, environment variables,
boolean/integer/float parsing, and error handling.
"""

import os
import pytest

from app.calculator_config import CalculatorConfig
from app.exceptions import ConfigurationError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def env_file(tmp_path):
    """Create a temporary .env file and return its path."""
    env = tmp_path / ".env"
    env.write_text(
        "CALCULATOR_LOG_DIR=test_logs\n"
        "CALCULATOR_LOG_FILE=test_calc.log\n"
        "CALCULATOR_HISTORY_DIR=test_data\n"
        "CALCULATOR_MAX_HISTORY_SIZE=500\n"
        "CALCULATOR_AUTO_SAVE=true\n"
        "CALCULATOR_PRECISION=3\n"
        "CALCULATOR_MAX_INPUT_VALUE=1e5\n"
        "CALCULATOR_DEFAULT_ENCODING=utf-16\n"
    )
    return str(env)


@pytest.fixture(autouse=True)
def clean_env():
    """Remove calculator-related env vars before and after each test."""
    keys = [
        "CALCULATOR_LOG_DIR", "CALCULATOR_LOG_FILE", "CALCULATOR_HISTORY_DIR",
        "CALCULATOR_MAX_HISTORY_SIZE", "CALCULATOR_AUTO_SAVE", "CALCULATOR_PRECISION",
        "CALCULATOR_MAX_INPUT_VALUE", "CALCULATOR_DEFAULT_ENCODING"
    ]
    saved = {}
    for k in keys:
        saved[k] = os.environ.pop(k, None)
    yield
    for k in keys:
        if saved[k] is not None:
            os.environ[k] = saved[k]
        else:
            os.environ.pop(k, None)


# ---------------------------------------------------------------------------
# Loading from .env
# ---------------------------------------------------------------------------


class TestConfigLoading:
    """Tests for loading configuration."""

    def test_defaults(self, tmp_path) -> None:
        """Without a .env file, defaults are used."""
        cfg = CalculatorConfig(env_path=str(tmp_path / "nonexistent.env"))
        assert cfg.log_dir == "logs"
        assert cfg.log_file == "calculator.log"
        assert cfg.history_dir == "data"
        assert cfg.max_history_size == 1000
        assert cfg.auto_save is True
        assert cfg.precision == 2
        assert cfg.max_input_value == 1e10
        assert cfg.default_encoding == "utf-8"

    def test_load_from_env_file(self, env_file: str) -> None:
        """Values from the .env file are loaded correctly."""
        cfg = CalculatorConfig(env_path=env_file)
        assert cfg.log_dir == "test_logs"
        assert cfg.log_file == "test_calc.log"
        assert cfg.history_dir == "test_data"
        assert cfg.max_history_size == 500
        assert cfg.auto_save is True
        assert cfg.precision == 3
        assert cfg.max_input_value == 1e5
        assert cfg.default_encoding == "utf-16"

    def test_repr(self, env_file: str) -> None:
        """Repr includes all settings."""
        cfg = CalculatorConfig(env_path=env_file)
        r = repr(cfg)
        assert "test_logs" in r
        assert "test_calc.log" in r
        assert "precision=3" in r


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestParsers:
    def test_parse_non_negative_int(self):
        assert CalculatorConfig._parse_non_negative_int("0", "TEST") == 0
        assert CalculatorConfig._parse_non_negative_int("10", "TEST") == 10
        with pytest.raises(ConfigurationError):
            CalculatorConfig._parse_non_negative_int("-1", "TEST")
        with pytest.raises(ConfigurationError):
            CalculatorConfig._parse_non_negative_int("abc", "TEST")

    def test_parse_float(self):
        assert CalculatorConfig._parse_float("1.5", "TEST") == 1.5
        assert CalculatorConfig._parse_float("1e10", "TEST") == 1e10
        with pytest.raises(ConfigurationError):
            CalculatorConfig._parse_float("abc", "TEST")
