"""
Pytest Fixtures and Test Environment Setup for Brightloop Nexus.
Automatically initializes database schema and seeds initial roles and admin.
Supports live MySQL if available or resilient SQLite testing engine.
"""
import pytest
from sqlalchemy import text
from app.core.database import engine, Base, SessionLocal
from app.core.config import settings
from app.services.auth_service import AuthService
from app.models import *  # Discover all application models


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """Ensure database schema is created and seeded before any tests run."""
    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
    except Exception:
        # If default connection fails, switch engine to SQLite test database
        from sqlalchemy import create_engine
        from app.core import database
        test_uri = "sqlite:///./test_brightloop.db"
        database.engine = create_engine(test_uri, connect_args={"check_same_thread": False})
        database.SessionLocal.configure(bind=database.engine)
        settings.DATABASE_URL = test_uri

    # Create all tables
    from app.core.database import engine as active_engine, SessionLocal as active_session
    Base.metadata.create_all(bind=active_engine)

    # Seed roles and admin
    db = active_session()
    try:
        AuthService.seed_initial_roles_and_admin(db)
    finally:
        db.close()

    yield

    # Teardown if sqlite
    if "sqlite" in settings.SQLALCHEMY_DATABASE_URI:
        Base.metadata.drop_all(bind=active_engine)

