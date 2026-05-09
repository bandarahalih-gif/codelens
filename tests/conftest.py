"""Shared test fixtures for CodeLens."""

import pytest
from src.app import create_app
from src.models import db as _db


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"
    MIMO_API_KEY = "test-key"
    MIMO_BASE_URL = "http://localhost:9999"
    MIMO_MODEL = "MiMo-v2.5-test"
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
