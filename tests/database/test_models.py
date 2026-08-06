import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.user import User
from app.models.product import Product
from app.models.analysis import Analysis
from app.models.review import Review


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    user = User(
        email="test_models@example.com",
        username="test_models_user",
        hashed_password="hashed_password",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    assert user.role == "seller"
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
    return user


def test_product_and_analysis_relationship(db_session, test_user):
    product = Product(
        user_id=test_user.id,
        product_url="https://www.daraz.lk/products/p1.html",
        product_title="Wireless Headphones",
        platform="Daraz",
        overall_rating=4.5,
        total_reviews=10
    )
    db_session.add(product)
    db_session.commit()

    analysis = Analysis(
        user_id=test_user.id,
        public_id="anl_test123",
        product_id=product.id,
        quality_risk_score=15.0,
        delivery_risk_score=20.0,
        trust_risk_score=10.0,
        business_risk_index=15.0,
        business_risk_level="LOW",
        total_reviews=10,
        total_positive_reviews=8,
        total_negative_reviews=1,
        total_neutral_reviews=1,
        average_confidence=0.92
    )
    db_session.add(analysis)
    db_session.commit()

    review = Review(
        user_id=test_user.id,
        analysis_id=analysis.id,
        review_text="Great sound quality!",
        sentiment="POSITIVE",
        confidence_score=0.95
    )
    db_session.add(review)
    db_session.commit()

    # Query Product and check relationships
    fetched_product = db_session.query(Product).filter_by(product_url="https://www.daraz.lk/products/p1.html").first()
    assert fetched_product is not None
    assert len(fetched_product.analyses) == 1
    assert fetched_product.analyses[0].public_id == "anl_test123"

    # Query Analysis and check reviews relationship
    fetched_analysis = db_session.query(Analysis).filter_by(public_id="anl_test123").first()
    assert fetched_analysis is not None
    assert len(fetched_analysis.reviews) == 1
    assert fetched_analysis.reviews[0].sentiment == "POSITIVE"


def test_cascade_deletion(db_session, test_user):
    product = Product(
        user_id=test_user.id,
        product_url="https://www.daraz.lk/products/p2.html",
        product_title="Smart Watch"
    )
    db_session.add(product)
    db_session.commit()

    analysis = Analysis(
        user_id=test_user.id,
        public_id="anl_test456",
        product_id=product.id,
        business_risk_level="MEDIUM"
    )
    db_session.add(analysis)
    db_session.commit()

    review = Review(
        user_id=test_user.id,
        analysis_id=analysis.id,
        review_text="Battery life is average."
    )
    db_session.add(review)
    db_session.commit()

    # Delete Analysis
    db_session.delete(analysis)
    db_session.commit()

    # Verify review was deleted via cascade
    assert db_session.query(Review).count() == 0
