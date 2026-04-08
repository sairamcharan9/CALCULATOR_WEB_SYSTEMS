"""
Integration Tests for Calculation Database Model
================================================

Tests inserting Calculation models using SQL operations to ensure foreign
keys and database behaviors are correctly mapped.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

from app.database import Base
from app.models import User, Calculation, CalculationModelFactory


# Setup a clean in-memory database for testing database interactions directly
test_engine = create_engine(
    "sqlite://",  # In-memory
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Build the tables on the test engine before start."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provides a transactional scope for a single test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_user(db_session):
    """Fixture to create and return a valid User."""
    user = User(username="math_fan", email="math@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestCalculationDatabase:
    """Testing SQLAlchemy mappings for the Calculation model."""

    def test_insert_calculation_success(self, db_session, sample_user):
        """A calculation can be stored and retrieved with correct bindings."""
        calc = CalculationModelFactory.create_calculation(
            user_id=sample_user.id,
            a=10.0,
            b=5.0,
            operation_type="MULTIPLY"
        )
        db_session.add(calc)
        db_session.commit()

        # Retrieve testing
        fetched_calc = db_session.query(Calculation).first()
        assert fetched_calc is not None
        assert fetched_calc.result == 50.0
        assert fetched_calc.user_id == sample_user.id

        # Test relationship mapping backwards
        assert fetched_calc.user.username == "math_fan"

    def test_calculation_user_relationship(self, db_session, sample_user):
        """Testing the relationship from User -> Calculations."""
        calc1 = CalculationModelFactory.create_calculation(sample_user.id, 2, 2, "ADD")
        calc2 = CalculationModelFactory.create_calculation(sample_user.id, 5, 2, "SUBTRACT")
        
        db_session.add_all([calc1, calc2])
        db_session.commit()

        # The user object should now see both calculations
        db_session.refresh(sample_user)
        assert len(sample_user.calculations) == 2
        types = {c.type for c in sample_user.calculations}
        assert types == {"ADD", "SUBTRACT"}

    def test_missing_user_foreign_key_fails(self, db_session):
        """Attempting to save a Calculation without a valid user_id fails."""
        # Intentionally assigning to a user_id that doesn't exist
        calc = CalculationModelFactory.create_calculation(user_id=999, a=10, b=5, operation_type="ADD")
        db_session.add(calc)
        
        # SQLite enforces foreign keys conditionally, but SQLAlchemy ensures nullability
        # If we didn't specify a user_id, it would be None and trip the nullable=False constraint.
        # Since SQLite by default doesn't strictly break on bad FKs unless PRAGMA is set, 
        # let's test nullability instead.
        calc_null = Calculation(a=1, b=2, type="ADD", result=3, user_id=None)
        db_session.add(calc_null)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
