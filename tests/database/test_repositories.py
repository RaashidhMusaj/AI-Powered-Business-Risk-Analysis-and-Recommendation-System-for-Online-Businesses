import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.user import User
from app.models.product import Product
from app.models.analysis import Analysis
from app.models.review import Review

from app.repositories.product_repository import ProductRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.health_repository import HealthRepository


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_user(db):
    user = User(
        email="repo_user@example.com",
        username="repo_user",
        hashed_password="hashed_password",
        full_name="Repo User"
    )
    db.add(user)
    db.commit()
    return user


def test_health_repository_connection(db):
    repo = HealthRepository(db=db)
    assert repo.check_db_connection() is True


def test_product_repository(db, test_user):
    product_repo = ProductRepository(db)
    
    # Create product
    product = Product(
        user_id=test_user.id,
        product_url="https://daraz.lk/products/item1.html",
        product_title="Gaming Mouse"
    )
    product_repo.add(product)
    db.commit()

    # Get product
    fetched = product_repo.get_by_url("https://daraz.lk/products/item1.html", user_id=test_user.id)
    assert fetched is not None
    assert fetched.product_title == "Gaming Mouse"


def test_analysis_repository_explicit_public_id_methods(db, test_user):
    product_repo = ProductRepository(db)
    analysis_repo = AnalysisRepository(db)

    product = product_repo.add(Product(user_id=test_user.id, product_url="https://daraz.lk/p2.html", product_title="Bluetooth Speaker"))
    db.commit()

    analysis = analysis_repo.add(
        Analysis(
            user_id=test_user.id,
            public_id="anl_pub123",
            product_id=product.id,
            business_risk_index=35.0,
            business_risk_level="MEDIUM"
        )
    )
    db.commit()

    # Test explicit get_by_public_id
    fetched = analysis_repo.get_by_public_id("anl_pub123", user_id=test_user.id)
    assert fetched is not None
    assert fetched.business_risk_level == "MEDIUM"

    # Test pagination & filtering
    items, total = analysis_repo.list_paginated(user_id=test_user.id, risk_level="MEDIUM")
    assert total == 1
    assert items[0].public_id == "anl_pub123"

    # Test explicit delete_by_public_id
    deleted = analysis_repo.delete_by_public_id("anl_pub123", user_id=test_user.id)
    db.commit()
    assert deleted is True

    assert analysis_repo.get_by_public_id("anl_pub123", user_id=test_user.id) is None


def test_service_transaction_rollback_simulation(db, test_user):
    product_repo = ProductRepository(db)
    analysis_repo = AnalysisRepository(db)

    try:
        product = product_repo.add(Product(user_id=test_user.id, product_url="https://daraz.lk/p3.html", product_title="Tablet"))
        analysis_repo.add(Analysis(user_id=test_user.id, public_id="anl_fail", product_id=product.id, business_risk_level="HIGH"))
        
        # Simulate unexpected error before commit
        raise RuntimeError("Simulated transaction failure")
    except Exception:
        db.rollback()

    # Verify rollback succeeded and database remains clean
    assert analysis_repo.get_by_public_id("anl_fail", user_id=test_user.id) is None
    assert product_repo.get_by_url("https://daraz.lk/p3.html", user_id=test_user.id) is None
