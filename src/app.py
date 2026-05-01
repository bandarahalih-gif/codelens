"""Flask application factory and route definitions."""

import os
import logging
from datetime import date, timedelta

from flask import Flask, jsonify, render_template, request
from src.config import Config
from src.models import Finding, Review, TokenUsage, db
from src.analyzer import Analyzer, detect_language
from src.mimo_client import MiMoClient
from src.utils import allowed_file, format_tokens, severity_badge

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Application factory."""
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    db.init_app(app)

    # Initialize MiMo client
    mimo = MiMoClient(
        api_key=app.config["MIMO_API_KEY"],
        base_url=app.config["MIMO_BASE_URL"],
        model=app.config["MIMO_MODEL"],
    )
    analyzer = Analyzer(mimo_client=mimo, app=app)

    with app.app_context():
        db.create_all()

    # --- Template filters ---
    @app.template_filter("timeago")
    def timeago_filter(dt):
        if not dt:
            return "never"
        diff = date.today() - dt.date() if hasattr(dt, "date") else date.today() - dt
        if diff.days == 0:
            return "today"
        if diff.days == 1:
            return "yesterday"
        if diff.days < 7:
            return f"{diff.days} days ago"
        if diff.days < 30:
            return f"{diff.days // 7} weeks ago"
        return f"{diff.days // 30} months ago"

    @app.template_filter("fmt_tokens")
    def fmt_tokens_filter(n):
        return format_tokens(n or 0)

    # --- Web Routes ---
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        reviews = Review.query.order_by(Review.created_at.desc()).limit(50).all()
        # Token usage last 7 days
        week_ago = date.today() - timedelta(days=7)
        token_history = TokenUsage.query.filter(TokenUsage.date >= week_ago).order_by(TokenUsage.date).all()
        total_tokens_week = sum(t.total_tokens for t in token_history)
        total_reviews_week = sum(t.review_count for t in token_history)
        return render_template("dashboard.html",
                               reviews=reviews,
                               token_history=token_history,
                               total_tokens_week=total_tokens_week,
                               total_reviews_week=total_reviews_week)

    @app.route("/review/<int:review_id>")
    def review_detail(review_id):
        review = Review.query.get_or_404(review_id)
        findings = Finding.query.filter_by(review_id=review_id).order_by(
            Finding.severity.desc(), Finding.line_start
        ).all()
        return render_template("review.html", review=review, findings=findings)

    @app.route("/settings")
    def settings():
        return render_template("settings.html",
                               api_key_set=bool(app.config.get("MIMO_API_KEY")),
                               base_url=app.config.get("MIMO_BASE_URL", ""),
                               model=app.config.get("MIMO_MODEL", ""),
                               daily_budget=app.config.get("DAILY_TOKEN_BUDGET", 0))

    # --- API Routes ---
    @app.route("/api/v1/review", methods=["POST"])
    def api_create_review():
        """Create a new code review via API."""
        data = request.get_json(silent=True) or {}
        source_code = data.get("code", "")
        filename = data.get("filename", "unknown.py")
        language = data.get("language")

        if not source_code:
            # Check for file upload
            if "file" in request.files:
                f = request.files["file"]
                if not allowed_file(f.filename):
                    return jsonify({"error": f"Unsupported file type: {f.filename}"}), 400
                source_code = f.read().decode("utf-8", errors="replace")
                filename = f.filename
            else:
                return jsonify({"error": "No code provided. Send 'code' in JSON body or upload a file."}), 400

        if len(source_code) > Config.MAX_FILE_SIZE:
            return jsonify({"error": f"File too large (max {Config.MAX_FILE_SIZE // 1024}KB)"}), 400

        try:
            review = analyzer.analyze(source_code, filename, language)
            return jsonify(review.to_dict()), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.exception("Review failed")
            return jsonify({"error": "Analysis failed", "detail": str(e)}), 500

    @app.route("/api/v1/reviews", methods=["GET"])
    def api_list_reviews():
        """List recent reviews."""
        limit = request.args.get("limit", 20, type=int)
        reviews = Review.query.order_by(Review.created_at.desc()).limit(limit).all()
        return jsonify([r.to_dict() for r in reviews])

    @app.route("/api/v1/reviews/<int:review_id>", methods=["GET"])
    def api_get_review(review_id):
        """Get review details with findings."""
        review = Review.query.get_or_404(review_id)
        findings = Finding.query.filter_by(review_id=review_id).all()
        return jsonify({**review.to_dict(), "findings": [f.to_dict() for f in findings]})

    @app.route("/api/v1/stats", methods=["GET"])
    def api_stats():
        """Usage statistics."""
        today = date.today()
        today_usage = TokenUsage.query.filter_by(date=today).first()
        week_ago = today - timedelta(days=7)
        week_usage = TokenUsage.query.filter(TokenUsage.date >= week_ago).all()

        total_reviews = Review.query.count()
        total_tokens = sum(u.total_tokens for u in TokenUsage.query.all())

        return jsonify({
            "today": today_usage.to_dict() if today_usage else {"total_tokens": 0, "review_count": 0},
            "week": {"total_tokens": sum(u.total_tokens for u in week_usage), "review_count": sum(u.review_count for u in week_usage)},
            "all_time": {"total_reviews": total_reviews, "total_tokens": total_tokens},
        })

    # --- Upload endpoint (form-based) ---
    @app.route("/upload", methods=["POST"])
    def upload_review():
        """Handle form-based code upload."""
        source_code = request.form.get("code", "")
        filename = request.form.get("filename", "pasted_code.py")

        if "file" in request.files and request.files["file"].filename:
            f = request.files["file"]
            if not allowed_file(f.filename):
                return render_template("index.html", error=f"Unsupported file type: {f.filename}")
            source_code = f.read().decode("utf-8", errors="replace")
            filename = f.filename

        if not source_code.strip():
            return render_template("index.html", error="No code provided")

        try:
            review = analyzer.analyze(source_code, filename)
            return render_template("review.html", review=review,
                                   findings=Finding.query.filter_by(review_id=review.id).order_by(Finding.severity.desc()).all())
        except ValueError as e:
            return render_template("index.html", error=str(e))
        except Exception as e:
            logger.exception("Upload review failed")
            return render_template("index.html", error=f"Analysis failed: {e}")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
