"""
Calculation API Routes (BREAD)
===============================

Implements Browse, Read, Edit, Add, and Delete endpoints for Calculation records.
All routes require a valid JWT Bearer token — the authenticated user's ID is used
automatically to scope reads and enforce ownership on mutations.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.database import get_db
from app.api.models import Calculation, CalculationModelFactory, User
from app.api.schemas import CalculationCreate, CalculationRead, CalculationUpdate, CalculationPatch
from app.api.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calculations", tags=["calculations"])


# ─────────────────────────────────────────────────────────────────────────────
# B — Browse: list all calculations for the logged-in user
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[CalculationRead], summary="Browse my calculations")
def browse_calculations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all calculations belonging to the currently authenticated user."""
    return (
        db.query(Calculation)
        .filter(Calculation.user_id == current_user.id)
        .order_by(Calculation.id.desc())
        .all()
    )


# ─────────────────────────────────────────────────────────────────────────────
# R — Read: retrieve one calculation by ID
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{calculation_id}", response_model=CalculationRead, summary="Read one calculation")
def read_calculation(
    calculation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a single calculation by its primary key.
    Returns 404 if not found, 403 if the calculation belongs to another user.
    """
    calc = db.query(Calculation).filter(Calculation.id == calculation_id).first()
    if calc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calculation with id={calculation_id} not found.",
        )
    if calc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this calculation.",
        )
    return calc


# ─────────────────────────────────────────────────────────────────────────────
# A — Add: create a new calculation
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/", response_model=CalculationRead, status_code=status.HTTP_201_CREATED,
             summary="Add a new calculation")
def add_calculation(
    payload: CalculationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new calculation record for the authenticated user.

    The result is computed server-side from `a`, `b`, and `type`.
    Division by zero is rejected at the schema level (422).
    The `user_id` is automatically set from the JWT — do not pass it in the body.
    """
    try:
        calc = CalculationModelFactory.create_calculation(
            user_id=current_user.id,
            a=payload.a,
            b=payload.b,
            operation_type=payload.type.value,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    db.add(calc)
    db.commit()
    db.refresh(calc)

    logger.info("Created calculation id=%d for user_id=%d", calc.id, calc.user_id)
    return calc


# ─────────────────────────────────────────────────────────────────────────────
# E — Edit (PUT): fully replace an existing calculation
# ─────────────────────────────────────────────────────────────────────────────

@router.put("/{calculation_id}", response_model=CalculationRead, summary="Edit a calculation (full)")
def edit_calculation(
    calculation_id: int,
    payload: CalculationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Replace an existing calculation's operands and operation type.
    The result is recomputed server-side.
    Returns 404 if not found, 403 if owned by another user.
    """
    calc = db.query(Calculation).filter(Calculation.id == calculation_id).first()
    if calc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calculation with id={calculation_id} not found.",
        )
    if calc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this calculation.",
        )

    try:
        updated = CalculationModelFactory.create_calculation(
            user_id=calc.user_id,
            a=payload.a,
            b=payload.b,
            operation_type=payload.type.value,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    calc.a = updated.a
    calc.b = updated.b
    calc.type = updated.type
    calc.result = updated.result

    db.commit()
    db.refresh(calc)

    logger.info("Updated calculation id=%d for user_id=%d", calc.id, current_user.id)
    return calc


# ─────────────────────────────────────────────────────────────────────────────
# E — Edit (PATCH): partially update an existing calculation
# ─────────────────────────────────────────────────────────────────────────────

@router.patch("/{calculation_id}", response_model=CalculationRead, summary="Edit a calculation (partial)")
def patch_calculation(
    calculation_id: int,
    payload: CalculationPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially update an existing calculation.
    Only the provided fields are changed; omitted fields keep their current values.
    The result is recomputed from the final merged operands/operation.
    """
    calc = db.query(Calculation).filter(Calculation.id == calculation_id).first()
    if calc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calculation with id={calculation_id} not found.",
        )
    if calc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this calculation.",
        )

    new_a = payload.a if payload.a is not None else calc.a
    new_b = payload.b if payload.b is not None else calc.b
    new_type = payload.type.value if payload.type is not None else calc.type

    try:
        updated = CalculationModelFactory.create_calculation(
            user_id=calc.user_id,
            a=new_a,
            b=new_b,
            operation_type=new_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    calc.a = updated.a
    calc.b = updated.b
    calc.type = updated.type
    calc.result = updated.result

    db.commit()
    db.refresh(calc)

    logger.info("Patched calculation id=%d for user_id=%d", calc.id, current_user.id)
    return calc


# ─────────────────────────────────────────────────────────────────────────────
# D — Delete: remove a calculation
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{calculation_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a calculation")
def delete_calculation(
    calculation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete a calculation record.
    Returns 204 on success, 404 if not found, 403 if owned by another user.
    """
    calc = db.query(Calculation).filter(Calculation.id == calculation_id).first()
    if calc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calculation with id={calculation_id} not found.",
        )
    if calc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this calculation.",
        )

    db.delete(calc)
    db.commit()

    logger.info("Deleted calculation id=%d for user_id=%d", calculation_id, current_user.id)
