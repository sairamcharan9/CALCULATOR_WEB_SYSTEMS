"""
Pydantic Schemas
================

Defines request/response schemas for User and Calculation operations.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator


# ---------------------------------------------------------------------------
# User Schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Schema for user login requests."""
    username: str
    password: str


class UserRead(BaseModel):
    """Schema for returning user data in API responses. Excludes password_hash."""
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT token response returned by /login."""
    access_token: str
    token_type: str = "bearer"



# ---------------------------------------------------------------------------
# Calculation Schemas
# ---------------------------------------------------------------------------

class OperationType(str, Enum):
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    INT_DIVIDE = "INT_DIVIDE"


class CalculationCreate(BaseModel):
    """
    Core schema for validating incoming calculation data (no user_id).
    Used for unit tests and as the base for HTTP request bodies.
    """
    a: float
    b: float
    type: OperationType

    @model_validator(mode='after')
    def check_division_by_zero(self):
        if self.type in (OperationType.DIVIDE, OperationType.INT_DIVIDE) and self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self


class CalculationRequest(CalculationCreate):
    """HTTP request body for POST /calculations. Adds user_id to CalculationCreate."""
    user_id: int


class CalculationUpdate(BaseModel):
    """HTTP request body for PUT /calculations/{id}."""
    a: float
    b: float
    type: OperationType

    @model_validator(mode='after')
    def check_division_by_zero(self):
        if self.type in (OperationType.DIVIDE, OperationType.INT_DIVIDE) and self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self


class CalculationPatch(BaseModel):
    """HTTP request body for PATCH /calculations/{id} — all fields optional."""
    a: Optional[float] = None
    b: Optional[float] = None
    type: Optional[OperationType] = None

    @model_validator(mode='after')
    def check_division_by_zero(self):
        op = self.type
        b = self.b
        if op in (OperationType.DIVIDE, OperationType.INT_DIVIDE) and b == 0:
            raise ValueError("Cannot divide by zero")
        return self


class CalculationRead(BaseModel):
    """Schema for returning calculation records in API responses."""
    id: int
    a: float
    b: float
    type: str
    result: float
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
