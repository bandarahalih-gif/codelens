"""Tests for the code analyzer engine."""

import pytest
from unittest.mock import MagicMock, patch
from src.analyzer import Analyzer, detect_language, compute_hash
from src.models import db, Review, Finding


class TestDetectLanguage:
    def test_python(self):
        assert detect_language("app.py") == "python"

    def test_javascript(self):
        assert detect_language("index.js") == "javascript"

    def test_go(self):
        assert detect_language("main.go") == "go"

    def test_unknown(self):
        assert detect_language("README.md") is None


class TestComputeHash:
    def test_deterministic(self):
        assert compute_hash("hello") == compute_hash("hello")

    def test_different_inputs(self):
        assert compute_hash("hello") != compute_hash("world")


class TestAnalyzer:
    def test_analyze_creates_review(self, app, db):
        mock_mimo = MagicMock()
        mock_mimo.analyze_code.return_value = {
            "findings": [
                {
                    "category": "security",
                    "severity": "high",
                    "title": "SQL Injection",
                    "description": "User input used in query",
                    "line_start": 10,
                    "line_end": 10,
                    "suggestion": "Use parameterized queries",
                    "cwe_id": "CWE-89",
                }
            ],
            "tokens_used": 5000,
            "prompt_tokens": 3000,
            "completion_tokens": 2000,
        }

        with app.app_context():
            analyzer = Analyzer(mock_mimo)
            review = analyzer.analyze("SELECT * FROM users WHERE id = " + "user_input", "test.py", "python")

            assert review.status == "complete"
            assert review.total_findings == 1
            assert review.high_count == 1
            assert review.tokens_used == 5000

            findings = Finding.query.filter_by(review_id=review.id).all()
            assert len(findings) == 1
            assert findings[0].cwe_id == "CWE-89"

    def test_analyze_handles_api_error(self, app, db):
        mock_mimo = MagicMock()
        mock_mimo.analyze_code.side_effect = Exception("API timeout")

        with app.app_context():
            analyzer = Analyzer(mock_mimo)
            with pytest.raises(Exception, match="API timeout"):
                analyzer.analyze("print(1)", "test.py")

            review = Review.query.first()
            assert review.status == "failed"
