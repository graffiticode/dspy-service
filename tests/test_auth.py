"""Authentication on protected routes: a missing key fails closed, and only the configured key is accepted."""

import pytest
from fastapi.testclient import TestClient

import src.main as main

client = TestClient(main.app)
PROTECTED = "/compile-prompt-spec"


@pytest.fixture
def auth(monkeypatch):
    def configure(key="", dev=False):
        monkeypatch.setattr(main.settings, "internal_api_key", key)
        monkeypatch.setattr(main.settings, "allow_unauthenticated_dev", dev)

    return configure


def post(headers=None):
    return client.post(PROTECTED, json={}, headers=headers or {})


def test_no_key_configured_refuses_protected_routes(auth):
    auth(key="", dev=False)
    assert post().status_code == 503
    assert post({"X-API-Key": "anything"}).status_code == 503


def test_no_key_configured_still_serves_public_paths(auth):
    auth(key="", dev=False)
    assert client.get("/health").status_code == 200


def test_dev_mode_is_explicit(auth):
    auth(key="", dev=True)
    assert post().status_code == 422


def test_configured_key_refuses_missing_and_wrong_keys(auth):
    auth(key="current-key")
    assert post().status_code == 401
    for wrong in ["old-key", "current-ke", "current-key2", "CURRENT-KEY"]:
        assert post({"X-API-Key": wrong}).status_code == 403


def test_configured_key_accepts_header_and_bearer(auth):
    auth(key="current-key")
    # Authenticated: reaches the route, which rejects the empty body as invalid (422), not as unauthorized.
    assert post({"X-API-Key": "current-key"}).status_code == 422
    assert post({"Authorization": "Bearer current-key"}).status_code == 422
