
import pytest
from app.calculator_repl import Calculator

def test_history_format_unary(tmp_path):
    env = tmp_path / ".env"
    env.write_text("AUTO_SAVE=false\n")
    calc = Calculator(env_path=str(env))
    
    calc.process_input("sqrt 9")
    history_text = calc.process_input("history")
    
    print(f"\nHistory text:\n{history_text}")
    
    # Correct format for unary: "  1. sqrt(9) = 3"
    # Incorrect format (if it took the if branch): "  1. 9 sqrt None = 3"
    assert "sqrt(9.0) = 3" in history_text or "sqrt(9) = 3" in history_text
    assert "None" not in history_text

if __name__ == "__main__":
    pytest.main([__file__])
