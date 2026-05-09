"""Tests for Flask routes."""

import json


class TestWebRoutes:
    def test_index(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"CodeLens" in resp.data

    def test_dashboard(self, client):
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        assert b"Dashboard" in resp.data

    def test_settings(self, client):
        resp = client.get("/settings")
        assert resp.status_code == 200
        assert b"Settings" in resp.data


class TestAPI:
    def test_create_review_no_code(self, client):
        resp = client.post("/api/v1/review", json={})
        assert resp.status_code == 400
        assert "No code" in resp.json["error"]

    def test_list_reviews(self, client):
        resp = client.get("/api/v1/reviews")
        assert resp.status_code == 200
        assert isinstance(resp.json, list)

    def test_stats(self, client):
        resp = client.get("/api/v1/stats")
        assert resp.status_code == 200
        assert "today" in resp.json
        assert "week" in resp.json
