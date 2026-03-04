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

    def test_parse_bool_valid_values(self):
        """_parse_bool accepts true/false/yes/no/1/0."""
        for truthy in ("true", "True", "TRUE", "1", "yes", "YES"):
            assert CalculatorConfig._parse_bool(truthy, "TEST") is True
        for falsy in ("false", "False", "FALSE", "0", "no", "NO"):
            assert CalculatorConfig._parse_bool(falsy, "TEST") is False

    def test_parse_bool_invalid_value(self):
        """_parse_bool raises ConfigurationError for unrecognised values."""
        with pytest.raises(ConfigurationError, match="Invalid boolean"):
            CalculatorConfig._parse_bool("maybe", "CALCULATOR_AUTO_SAVE")

    def test_parse_positive_int_valid(self):
        assert CalculatorConfig._parse_positive_int("1", "TEST") == 1
        assert CalculatorConfig._parse_positive_int("500", "TEST") == 500

    def test_parse_positive_int_zero_raises(self):
        """Zero is not a positive integer."""
        with pytest.raises(ConfigurationError, match="positive integer"):
            CalculatorConfig._parse_positive_int("0", "CALCULATOR_MAX_HISTORY_SIZE")

    def test_parse_positive_int_negative_raises(self):
        with pytest.raises(ConfigurationError):
            CalculatorConfig._parse_positive_int("-5", "CALCULATOR_MAX_HISTORY_SIZE")

    def test_parse_positive_int_non_numeric_raises(self):
        with pytest.raises(ConfigurationError, match="Invalid integer"):
            CalculatorConfig._parse_positive_int("abc", "CALCULATOR_MAX_HISTORY_SIZE")


# ---------------------------------------------------------------------------
# Startup validation — validate()
# ---------------------------------------------------------------------------


class TestValidation:
    """Tests for the validate() method called automatically on init."""

    def _make_env(self, tmp_path, **overrides) -> str:
        """Helper: write a valid .env then patch specific keys."""
        defaults = {
            "CALCULATOR_LOG_DIR": "logs",
            "CALCULATOR_LOG_FILE": "calculator.log",
            "CALCULATOR_HISTORY_DIR": "data",
            "CALCULATOR_HISTORY_FILE": "history.csv",
            "CALCULATOR_MAX_HISTORY_SIZE": "1000",
            "CALCULATOR_AUTO_SAVE": "true",
            "CALCULATOR_PRECISION": "2",
            "CALCULATOR_MAX_INPUT_VALUE": "1e10",
            "CALCULATOR_DEFAULT_ENCODING": "utf-8",
        }
        defaults.update(overrides)
        env = tmp_path / ".env"
        env.write_text("\n".join(f"{k}={v}" for k, v in defaults.items()))
        return str(env)

    def test_blank_log_dir_raises(self, tmp_path) -> None:
        env = self._make_env(tmp_path, CALCULATOR_LOG_DIR="   ")
        with pytest.raises(ConfigurationError, match="LOG_DIR"):
            CalculatorConfig(env_path=env)

    def test_blank_log_file_raises(self, tmp_path) -> None:
        env = self._make_env(tmp_path, CALCULATOR_LOG_FILE="")
        with pytest.raises(ConfigurationError, match="LOG_FILE"):
            CalculatorConfig(env_path=env)

    def test_blank_history_dir_raises(self, tmp_path) -> None:
        env = self._make_env(tmp_path, CALCULATOR_HISTORY_DIR="  ")
        with pytest.raises(ConfigurationError, match="HISTORY_DIR"):
            CalculatorConfig(env_path=env)

    def test_blank_history_file_raises(self, tmp_path) -> None:
        env = self._make_env(tmp_path, CALCULATOR_HISTORY_FILE="")
        with pytest.raises(ConfigurationError, match="HISTORY_FILE"):
            CalculatorConfig(env_path=env)

    def test_precision_too_high_raises(self, tmp_path) -> None:
        env = self._make_env(tmp_path, CALCULATOR_PRECISION="21")
        with pytest.raises(ConfigurationError, match="PRECISION"):
            CalculatorConfig(env_path=env)

    def test_precision_at_max_is_valid(self, tmp_path) -> None:
        env = self._make_env(tmp_path, CALCULATOR_PRECISION="20")
        cfg = CalculatorConfig(env_path=env)
        assert cfg.precision == 20

    def test_negative_max_input_value_raises(self, tmp_path) -> None:
        env = self._make_env(tmp_path, CALCULATOR_MAX_INPUT_VALUE="-1")
        with pytest.raises(ConfigurationError, match="MAX_INPUT_VALUE"):
            CalculatorConfig(env_path=env)

    def test_zero_max_input_value_raises(self, tmp_path) -> None:
        env = self._make_env(tmp_path, CALCULATOR_MAX_INPUT_VALUE="0")
        with pytest.raises(ConfigurationError, match="MAX_INPUT_VALUE"):
            CalculatorConfig(env_path=env)

    def test_unsupported_encoding_raises(self, tmp_path) -> None:
        env = self._make_env(tmp_path, CALCULATOR_DEFAULT_ENCODING="shift-jis")
        with pytest.raises(ConfigurationError, match="encoding"):
            CalculatorConfig(env_path=env)

    def test_valid_encodings_accepted(self, tmp_path) -> None:
        for enc in ("utf-8", "utf-16", "ascii", "latin-1"):
            env = self._make_env(tmp_path, CALCULATOR_DEFAULT_ENCODING=enc)
            cfg = CalculatorConfig(env_path=env)
            assert cfg.default_encoding == enc


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


class TestRepr:
    def test_repr_includes_all_fields(self, env_file: str) -> None:
        cfg = CalculatorConfig(env_path=env_file)
        r = repr(cfg)
        assert "test_logs" in r
        assert "test_calc.log" in r
        assert "test_data" in r
        assert "history.csv" in r
        assert "precision=3" in r
        assert "auto_save=True" in r
