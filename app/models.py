"""
SQLAlchemy User Model
====================

Defines the User table with secure password storage and unique constraints.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """
    User model for the application.

    Attributes:
        id: Primary key, auto-incremented.
        username: Unique username, required.
        email: Unique email address, required.
        password_hash: Bcrypt-hashed password, required.
        created_at: Timestamp when the user was created.
        calculations: A reverse relationship to all calculations by this user.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to Calculation records
    calculations = relationship("Calculation", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Calculation(Base):
    """
    Calculation model representing a single math operation.

    Attributes:
        id: Primary key.
        a: First operand.
        b: Second operand.
        type: The arithmetic operation (e.g., ADD, SUBTRACT, MULTIPLY, DIVIDE).
        result: The computed result.
        user_id: Foreign key string linking to the User.
        created_at: Automatic timestamp.
        user: SQLAlchemy relationship mapping.
    """
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    a = Column(Float, nullable=False)
    b = Column(Float, nullable=False)
    type = Column(String(20), nullable=False, index=True)
    result = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="calculations")

    def __repr__(self):
        return f"<Calculation(a={self.a}, b={self.b}, type='{self.type}', result={self.result})>"


class CalculationModelFactory:
    """
    A Factory for instantiating SQLAlchemy Calculation models.
    It computes the result based on the requested operation type.
    """

    @staticmethod
    def create_calculation(user_id: int, a: float, b: float, operation_type: str) -> Calculation:
        op = operation_type.upper()
        if op == "ADD":
            result = a + b
        elif op == "SUBTRACT":
            result = a - b
        elif op == "MULTIPLY":
            result = a * b
        elif op in ("DIVIDE", "INT_DIVIDE"):
            if b == 0:
                raise ValueError("Cannot divide by zero")
            result = a / b if op == "DIVIDE" else float(int(a) // int(b))
        else:
            raise ValueError(f"Unsupported calculation type: {operation_type}")

        return Calculation(
            a=a,
            b=b,
            type=op,
            result=result,
            user_id=user_id
        )
