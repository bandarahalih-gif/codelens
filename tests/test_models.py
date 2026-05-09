"""Tests for database models."""

from datetime import date
from src.models import db, Review, Finding, TokenUsage


class TestReview:
    def test_create_review(self, app, db):
        with app.app_context():
            review = Review(filename="test.py", language="python", source_hash="abc123")
            db.session.add(review)
            db.session.commit()
            assert review.id is not None
            assert review.status == "pending"

    def test_to_dict(self, app, db):
        with app.app_context():
            review = Review(filename="app.py", language="python", source_hash="def456", total_findings=3)
            db.session.add(review)
            db.session.commit()
            d = review.to_dict()
            assert d["filename"] == "app.py"
            assert d["total_findings"] == 3


class TestFinding:
    def test_create_finding(self, app, db):
        with app.app_context():
            review = Review(filename="test.py", language="python", source_hash="xyz")
            db.session.add(review)
            db.session.commit()

            finding = Finding(
                review_id=review.id,
                category="security",
                severity="critical",
                title="Hardcoded Secret",
                description="API key found in source",
            )
            db.session.add(finding)
            db.session.commit()
            assert finding.id is not None


class TestTokenUsage:
    def test_create_usage(self, app, db):
        with app.app_context():
            usage = TokenUsage(date=date.today(), total_tokens=50000, review_count=5, avg_tokens_per_review=10000)
            db.session.add(usage)
            db.session.commit()
            d = usage.to_dict()
            assert d["total_tokens"] == 50000
