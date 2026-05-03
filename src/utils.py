"""Utility functions for CodeLens."""

import os

from src.config import Config


def allowed_file(filename: str) -> bool:
    """Check if file extension is supported."""
    return "." in filename and         f".{filename.rsplit('.', 1)[1].lower()}" in Config.SUPPORTED_EXTENSIONS


def severity_color(severity: str) -> str:
    """Return CSS color class for severity level."""
    return {
        "critical": "#ef4444",
        "high": "#f97316",
        "medium": "#eab308",
        "low": "#22c55e",
    }.get(severity, "#6b7280")


def severity_badge(severity: str) -> str:
    """Return emoji badge for severity."""
    return {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }.get(severity, "⚪")


def format_tokens(n: int) -> str:
    """Format token count for display."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)
