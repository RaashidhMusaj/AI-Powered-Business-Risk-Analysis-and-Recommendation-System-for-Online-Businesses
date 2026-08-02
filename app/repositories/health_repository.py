from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.logger import db_logger


class HealthRepository:
    """
    Repository performing real database connectivity checks.
    """
    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def check_db_connection(self) -> bool:
        """
        Executes SELECT 1 query to verify active database connectivity.
        """
        if not self.db:
            return False
        try:
            self.db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            db_logger.warning(f"Database health check connection ping failed: {str(e)}")
            return False
