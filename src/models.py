"""SQLAlchemy models for CodeLens."""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Review(db.Model):
    """A code review submission."""

    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    source_hash = db.Column(db.String(64), nullable=False, index=True)
    status = db.Column(db.String(20), default="pending")  # pending, analyzing, complete, failed
    total_findings = db.Column(db.Integer, default=0)
    critical_count = db.Column(db.Integer, default=0)
    high_count = db.Column(db.Integer, default=0)
    medium_count = db.Column(db.Integer, default=0)
    low_count = db.Column(db.Integer, default=0)
    tokens_used = db.Column(db.Integer, default=0)
    analysis_time_ms = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    findings = db.relationship("Finding", backref="review", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "language": self.language,
            "status": self.status,
            "total_findings": self.total_findings,
            "critical": self.critical_count,
            "high": self.high_count,
            "medium": self.medium_count,
            "low": self.low_count,
            "tokens_used": self.tokens_used,
            "analysis_time_ms": self.analysis_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class Finding(db.Model):
    """An individual finding within a review."""

    __tablename__ = "findings"

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id"), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # bug, security, style, performance
    severity = db.Column(db.String(20), nullable=False)  # critical, high, medium, low
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    line_start = db.Column(db.Integer, nullable=True)
    line_end = db.Column(db.Integer, nullable=True)
    suggestion = db.Column(db.Text, nullable=True)
    cwe_id = db.Column(db.String(20), nullable=True)  # CWE-89, CWE-79, etc.

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "suggestion": self.suggestion,
            "cwe_id": self.cwe_id,
        }


class TokenUsage(db.Model):
    """Daily token usage tracking."""

    __tablename__ = "token_usage"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True, index=True)
    total_tokens = db.Column(db.Integer, default=0)
    review_count = db.Column(db.Integer, default=0)
    avg_tokens_per_review = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            "date": self.date.isoformat(),
            "total_tokens": self.total_tokens,
            "review_count": self.review_count,
            "avg_tokens_per_review": round(self.avg_tokens_per_review, 1),
        }
