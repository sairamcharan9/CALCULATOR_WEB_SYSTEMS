"""
CLI Macro Command Plugin
========================

Provides the 'macro' command to dynamically evaluate string-based formula macros
directly inside the interactive CLI REPL session.
"""

from colorama import Fore
from app.cli.commands import command
from app.api.macro_routes import eval_macro_expression


@command(
    "macro",
    "Evaluate custom macro formula expressions dynamically.",
    "macro <expression> [var=val]"
)
def macro_command(self, *args) -> str:
    """
    Evaluates dynamic macro expressions with optional keyword assignments.
    Example usage:
      macro add(power(a, 2), power(b, 2)) a=3 b=4
    """
    if not args:
        msg = "Error: Usage is 'macro <expression> [var=val]'"
        print(f"{Fore.RED}{msg}")
        return msg

    # Separate variable assignments (e.g. a=3) from the expression parts
    expr_parts = []
    variables = {}
    
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=", 1)
            try:
                variables[k.strip()] = float(v.strip())
            except ValueError:
                # If value is not float, treat as part of expression string
                expr_parts.append(arg)
        else:
            expr_parts.append(arg)

    expression = " ".join(expr_parts)
    if not expression.strip():
        msg = "Error: Macro expression cannot be empty."
        print(f"{Fore.RED}{msg}")
        return msg

    try:
        res = eval_macro_expression(expression, variables)
        formatted_res = f"{res:.12f}".rstrip("0").rstrip(".") if "." in f"{res:.12f}" else f"{res}"
        msg = f"Result: {formatted_res}"
        print(f"{Fore.GREEN}{msg}")
        return msg
    except Exception as e:
        msg = f"Error: {e}"
        print(f"{Fore.RED}{msg}")
        return msg
