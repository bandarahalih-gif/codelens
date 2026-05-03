"""Core code analysis engine — orchestrates MiMo calls and persists results."""

import hashlib
import logging
import time
from datetime import date, timezone
from datetime import datetime as dt

from src.models import Finding, Review, TokenUsage, db

logger = logging.getLogger(__name__)

# Language detection by extension
EXTENSION_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".go": "go", ".rs": "rust", ".java": "java",
    ".cpp": "cpp", ".c": "c", ".rb": "ruby", ".php": "php",
}


def detect_language(filename: str) -> str | None:
    """Detect programming language from filename extension."""
    for ext, lang in EXTENSION_MAP.items():
        if filename.endswith(ext):
            return lang
    return None


def compute_hash(source: str) -> str:
    """SHA-256 hash of source code for deduplication."""
    return hashlib.sha256(source.encode()).hexdigest()


class Analyzer:
    """Orchestrates code analysis using MiMo."""

    def __init__(self, mimo_client, app=None):
        self.mimo = mimo_client
        self.app = app

    def analyze(self, source_code: str, filename: str, language: str | None = None) -> Review:
        """Run full analysis pipeline on source code."""
        if not language:
            language = detect_language(filename)
        if not language:
            raise ValueError(f"Cannot detect language for: {filename}")

        source_hash = compute_hash(source_code)

        # Check for recent duplicate
        existing = Review.query.filter_by(source_hash=source_hash).order_by(Review.created_at.desc()).first()
        if existing and existing.status == "complete":
            logger.info("Returning cached review for %s (hash: %s)", filename, source_hash[:12])
            return existing

        # Create review record
        review = Review(
            filename=filename,
            language=language,
            source_hash=source_hash,
            status="analyzing",
        )
        db.session.add(review)
        db.session.commit()

        start_time = time.monotonic()

        try:
            result = self.mimo.analyze_code(source_code, language, filename)
            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            # Persist findings
            severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for f in result["findings"]:
                severity = f.get("severity", "medium").lower()
                if severity not in severity_counts:
                    severity = "medium"

                finding = Finding(
                    review_id=review.id,
                    category=f.get("category", "bug"),
                    severity=severity,
                    title=f.get("title", "Unknown issue"),
                    description=f.get("description", ""),
                    line_start=f.get("line_start"),
                    line_end=f.get("line_end"),
                    suggestion=f.get("suggestion"),
                    cwe_id=f.get("cwe_id"),
                )
                db.session.add(finding)
                severity_counts[severity] += 1

            # Update review
            review.status = "complete"
            review.total_findings = len(result["findings"])
            review.critical_count = severity_counts["critical"]
            review.high_count = severity_counts["high"]
            review.medium_count = severity_counts["medium"]
            review.low_count = severity_counts["low"]
            review.tokens_used = result["tokens_used"]
            review.analysis_time_ms = elapsed_ms
            review.completed_at = dt.now(timezone.utc)

            # Update daily token usage
            self._track_tokens(result["tokens_used"])

            db.session.commit()
            logger.info("Review #%d complete: %d findings, %d tokens, %dms",
                        review.id, review.total_findings, review.tokens_used, elapsed_ms)
            return review

        except Exception as e:
            review.status = "failed"
            db.session.commit()
            logger.error("Analysis failed for review #%d: %s", review.id, e)
            raise

    def _track_tokens(self, tokens: int):
        """Update daily token usage counter."""
        today = date.today()
        usage = TokenUsage.query.filter_by(date=today).first()
        if not usage:
            usage = TokenUsage(date=today, total_tokens=0, review_count=0, avg_tokens_per_review=0)
            db.session.add(usage)

        usage.total_tokens += tokens
        usage.review_count += 1
        usage.avg_tokens_per_review = usage.total_tokens / usage.review_count
