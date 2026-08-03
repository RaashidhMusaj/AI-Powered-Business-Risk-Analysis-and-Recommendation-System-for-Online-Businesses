from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import uuid
from datetime import datetime, timezone

from app.config.settings import settings
from app.utils.logger import db_logger

from app.database.base import Base
import app.models  # Ensure all models are registered

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine_kwargs = {"echo": False}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

DEFAULT_SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"
_schema_migrated = False


def ensure_schema_migrations():
    """Ensure missing columns in existing database tables are migrated and tenant isolation is enforced once per process."""
    global _schema_migrated
    if _schema_migrated:
        return

    try:
        with engine.begin() as conn:
            inspector = inspect(engine)
            table_names = inspector.get_table_names()

            # Ensure users table columns & system admin default user exist
            if "users" in table_names:
                user_cols = [c["name"].lower() for c in inspector.get_columns("users")]
                if "role" not in user_cols:
                    db_logger.info("Migrating users table: adding missing 'role' column...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(32) DEFAULT 'seller'"))
                if "failed_login_attempts" not in user_cols:
                    db_logger.info("Migrating users table: adding missing 'failed_login_attempts' column...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0"))
                if "locked_until" not in user_cols:
                    db_logger.info("Migrating users table: adding missing 'locked_until' column...")
                    dt_type = "DATETIME" if is_sqlite else "TIMESTAMP"
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN locked_until {dt_type}"))

                now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                if is_sqlite:
                    conn.execute(text(f"""
                        INSERT OR IGNORE INTO users (id, created_at, updated_at, email, username, hashed_password, full_name, role, is_active, failed_login_attempts)
                        VALUES ('{DEFAULT_SYSTEM_USER_ID}', '{now_iso}', '{now_iso}', 'system@local', 'system_admin', 'hashed_system', 'System Admin', 'admin', 1, 0)
                    """))
                else:
                    conn.execute(text(f"""
                        INSERT INTO users (id, created_at, updated_at, email, username, hashed_password, full_name, role, is_active, failed_login_attempts)
                        VALUES ('{DEFAULT_SYSTEM_USER_ID}', '{now_iso}', '{now_iso}', 'system@local', 'system_admin', 'hashed_system', 'System Admin', 'admin', true, 0)
                        ON CONFLICT (id) DO NOTHING
                    """))

            col_type = "CHAR(36)" if is_sqlite else "UUID"

            # Column additions for products
            if "products" in table_names:
                cols = [c["name"].lower() for c in inspector.get_columns("products")]
                if "seller_name" not in cols:
                    conn.execute(text("ALTER TABLE products ADD COLUMN seller_name VARCHAR(256)"))
                if "image_url" not in cols:
                    conn.execute(text("ALTER TABLE products ADD COLUMN image_url VARCHAR(2048)"))
                if "external_product_id" not in cols:
                    conn.execute(text("ALTER TABLE products ADD COLUMN external_product_id VARCHAR(128)"))
                if "current_price" not in cols:
                    conn.execute(text("ALTER TABLE products ADD COLUMN current_price VARCHAR(64)"))
                if "user_id" not in cols:
                    db_logger.info("Migrating products table: adding missing 'user_id' column...")
                    conn.execute(text(f"ALTER TABLE products ADD COLUMN user_id {col_type}"))
                    conn.execute(text(f"UPDATE products SET user_id = '{DEFAULT_SYSTEM_USER_ID}' WHERE user_id IS NULL"))

            # Column additions for analyses
            if "analyses" in table_names:
                cols = [c["name"].lower() for c in inspector.get_columns("analyses")]
                if "business_risk_snapshot" not in cols:
                    conn.execute(text("ALTER TABLE analyses ADD COLUMN business_risk_snapshot JSON"))
                if "recommendation_snapshot" not in cols:
                    conn.execute(text("ALTER TABLE analyses ADD COLUMN recommendation_snapshot JSON"))
                if "user_id" not in cols:
                    db_logger.info("Migrating analyses table: adding missing 'user_id' column...")
                    conn.execute(text(f"ALTER TABLE analyses ADD COLUMN user_id {col_type}"))
                    conn.execute(text(f"UPDATE analyses SET user_id = '{DEFAULT_SYSTEM_USER_ID}' WHERE user_id IS NULL"))

            # Column additions for reviews
            if "reviews" in table_names:
                cols = [c["name"].lower() for c in inspector.get_columns("reviews")]
                if "user_id" not in cols:
                    db_logger.info("Migrating reviews table: adding missing 'user_id' column...")
                    conn.execute(text(f"ALTER TABLE reviews ADD COLUMN user_id {col_type}"))
                    conn.execute(text(f"UPDATE reviews SET user_id = '{DEFAULT_SYSTEM_USER_ID}' WHERE user_id IS NULL"))

            _schema_migrated = True
            db_logger.info("Schema migration check completed successfully.")
    except Exception as err:
        db_logger.error(f"Auto column migration error: {err}")


# Ensure tables exist and schema columns are up to date
try:
    Base.metadata.create_all(bind=engine)
    ensure_schema_migrations()
except Exception as err:
    db_logger.warning(f"Could not auto-create tables / migrate schema: {err}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency generator for database sessions.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db_logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
