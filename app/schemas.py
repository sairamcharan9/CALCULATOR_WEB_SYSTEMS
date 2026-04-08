"""
Pydantic Schemas
================

Defines request/response schemas for User operations.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    """
    Schema for creating a new user.

    Fields:
        username: The desired username (required).
        email: A valid email address (required).
        password: The plain-text password (required, will be hashed before storage).
    """
    username: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    """
    Schema for returning user data in API responses.
    Intentionally excludes password_hash for security.

    Fields:
        id: The user's database ID.
        username: The user's username.
        email: The user's email address.
        created_at: When the user account was created.
    """
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


from enum import Enum
from pydantic import model_validator


class OperationType(str, Enum):
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    INT_DIVIDE = "INT_DIVIDE"


class CalculationCreate(BaseModel):
    """
    Schema for validating incoming calculation requests.
    Validates operand types, operation type enum, and division by zero.
    """
    a: float
    b: float
    type: OperationType

    @model_validator(mode='after')
    def check_division_by_zero(self):
        # self is the instantiated model 
        if self.type in (OperationType.DIVIDE, OperationType.INT_DIVIDE) and self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self


class CalculationRead(BaseModel):
    """
    Schema for returning calculation records in API responses.
    """
    id: int
    a: float
    b: float
    type: str
    result: float
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
