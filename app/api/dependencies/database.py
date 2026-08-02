from typing import Generator
from sqlalchemy.orm import Session
from app.database.session import get_db_session


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency injecting database session.
    """
    yield from get_db_session()
