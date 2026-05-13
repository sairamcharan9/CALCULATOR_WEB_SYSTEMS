"""
Dynamic User-Defined Formula Macros API Routes
==============================================

Allows users to create, store, execute, and delete complex multi-variable custom formulas.
Implements a secure recursive descent parser engine server-side utilizing existing
Command/Strategy patterns to evaluate nested functions dynamically.
"""

import logging
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.models import CustomFormula, User, Calculation
from app.api.schemas import CustomFormulaCreate, CustomFormulaRead, MacroExecuteRequest
from app.api.security import get_current_user
from app.cli.command_loader import command_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/macros", tags=["macros"])


def eval_macro_expression(expr: str, variables: dict[str, float]) -> float:
    """
    Recursively breaks down string-based macro expressions into nested base operations.
    Utilizes registered commands in CommandManager for calculation logic.
    """
    expr = expr.strip()
    if not expr:
        raise ValueError("Empty macro expression encountered.")

    # 1. Check if it's a simple literal float/int
    try:
        return float(expr)
    except ValueError:
        pass

    # 2. Check if it's a defined variable
    if expr in variables:
        return float(variables[expr])

    # 3. Must be a function call: func_name(arg1, arg2, ...)
    open_paren = expr.find('(')
    if open_paren == -1 or not expr.endswith(')'):
        raise ValueError(f"Unknown variable or invalid expression syntax: '{expr}'")

    func_name = expr[:open_paren].strip().lower()
    # Map friendly alias
    if func_name == "pow":
        func_name = "power"

    args_str = expr[open_paren + 1:-1].strip()

    # Tokenize arguments at top level of current parenthesis depth
    args = []
    current_arg = []
    depth = 0
    for char in args_str:
        if char == '(':
            depth += 1
            current_arg.append(char)
        elif char == ')':
            depth -= 1
            current_arg.append(char)
        elif char == ',' and depth == 0:
            args.append("".join(current_arg).strip())
            current_arg = []
        else:
            current_arg.append(char)

    if current_arg:
        args.append("".join(current_arg).strip())

    # Filter out empty arguments gracefully
    args = [a for a in args if a]

    # Recursively evaluate each argument
    evaluated_args = [eval_macro_expression(arg, variables) for arg in args]

    # Retrieve command logic via Strategy/Command Pattern Manager
    cmd = command_manager.get_command(func_name)
    if not cmd or not ("<" in cmd.usage and "[" not in cmd.usage):
        raise ValueError(f"Unsupported formula operation: '{func_name}'")

    # Execute using existing handler
    try:
        dec_args = [Decimal(str(val)) for val in evaluated_args]
        res = cmd.handler(*dec_args)
        return float(res)
    except Exception as exc:
        raise ValueError(f"Error evaluating '{func_name}': {exc}")


@router.post("/execute", summary="Dynamically calculate macro expressions")
@router.post("/execute/", summary="Dynamically calculate macro expressions")
def execute_macro(
    payload: MacroExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Executes a custom macro dynamically server-side.
    Accepts either an inline expression string OR a stored macro_id, along with a variable map.
    """
    expression_str = payload.expression

    if payload.macro_id is not None:
        macro = db.query(CustomFormula).filter(CustomFormula.id == payload.macro_id).first()
        if not macro:
            raise HTTPException(status_code=404, detail=f"Macro ID {payload.macro_id} not found.")
        if macro.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this macro.")
        expression_str = macro.expression

    if not expression_str:
        raise HTTPException(status_code=422, detail="Either expression or macro_id must be provided.")

    try:
        result = eval_macro_expression(expression_str, payload.variables)
        
        # Automatically record to calculation history if executing a stored macro
        if payload.macro_id is not None:
            macro_obj = db.query(CustomFormula).filter(CustomFormula.id == payload.macro_id).first()
            if macro_obj:
                op_label = f"⚡ {macro_obj.name}"[:20]
                a_val = float(payload.variables.get("a", 0.0))
                b_val = float(payload.variables.get("b", 0.0))
                calc_record = Calculation(
                    a=a_val,
                    b=b_val,
                    type=op_label,
                    result=result,
                    user_id=current_user.id
                )
                db.add(calc_record)
                db.commit()

        return {"result": result, "expression": expression_str, "variables": payload.variables}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/", response_model=CustomFormulaRead, status_code=status.HTTP_201_CREATED, summary="Create custom formula macro")
@router.post("", response_model=CustomFormulaRead, status_code=status.HTTP_201_CREATED, summary="Create custom formula macro")
def create_macro(
    payload: CustomFormulaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Stores a new custom multi-variable formula macro directly as a native operation.
    """
    # Validate expression syntax before saving using dummy/zero variables if possible, or simple check
    if not payload.name.strip() or not payload.expression.strip():
        raise HTTPException(status_code=422, detail="Formula name and expression are required.")

    # Check for duplicate formula name (case-insensitive) for this specific user
    existing = db.query(CustomFormula).filter(
        func.lower(CustomFormula.name) == payload.name.strip().lower(),
        CustomFormula.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="A formula with this name already exists.")

    formula = CustomFormula(
        name=payload.name.strip(),
        expression=payload.expression.strip(),
        user_id=current_user.id
    )
    db.add(formula)
    db.commit()
    db.refresh(formula)

    logger.info("Created macro ID %d for user_id %d", formula.id, current_user.id)
    return formula


@router.get("/", response_model=List[CustomFormulaRead], summary="List stored formula macros")
def list_macros(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all dynamic formula macros defined by the authenticated user.
    """
    return db.query(CustomFormula).filter(CustomFormula.user_id == current_user.id).order_by(CustomFormula.id.desc()).all()


@router.delete("/{macro_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete custom formula macro")
def delete_macro(
    macro_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Removes a stored custom formula macro.
    """
    macro = db.query(CustomFormula).filter(CustomFormula.id == macro_id).first()
    if not macro:
        raise HTTPException(status_code=404, detail="Macro formula not found.")
    if macro.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this macro.")

    db.delete(macro)
    db.commit()
    logger.info("Deleted macro ID %d by user %d", macro_id, current_user.id)
