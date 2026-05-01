"""Application configuration from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///codelens.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
    MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://api.mimo.xiaomi.com/v1")
    MIMO_MODEL = os.getenv("MIMO_MODEL", "MiMo-v2.5")

    MAX_FILE_SIZE = 512 * 1024  # 512KB
    SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c", ".rb", ".php"}

    # Token budget defaults
    DAILY_TOKEN_BUDGET = int(os.getenv("DAILY_TOKEN_BUDGET", "5000000"))
    REVIEW_TOKEN_LIMIT = int(os.getenv("REVIEW_TOKEN_LIMIT", "50000"))
