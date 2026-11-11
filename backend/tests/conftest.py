"""Shared fixtures for CrisisOS backend tests (iteration 5: security hardening).

All routes except /health /ready /auth/* require a Bearer token.
demo/reset is ADMIN-only (SEC-002); /api/ws requires ?token=JWT (SEC-003).
Role passwords come from backend env (DEMO_<ROLE>_PASSWORD) via
/app/memory/test_credentials.md — never hard-code new credentials elsewhere.
"""
import os
from pathlib import Path

import pytest
import requests


def _load_base_url() -> str:
    url = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL")
    if not url:
        for line in Path("/app/frontend/.env").read_text().splitlines():
            if line.startswith("EXPO_PUBLIC_BACKEND_URL="):
                url = line.split("=", 1)[1].strip().strip('"')
                break
    if not url:
        pytest.fail("EXPO_PUBLIC_BACKEND_URL is not set")
    return url.rstrip("/")


BASE_URL = _load_base_url()
API = f"{BASE_URL}/api"
WS_URL = f"{BASE_URL.replace('http', 'ws', 1)}/api/ws"

# Iteration 5: env-sourced demo passwords (see /app/memory/test_credentials.md).
CREDENTIALS = {
    "CITIZEN": ("citizen@crisisos.app", "Cs!1f726b5c18b4"),
    "RESPONDER": ("responder@crisisos.app", "Cs!582aeda87430"),
    "OPERATOR": ("operator@crisisos.app", "Cs!331720cf7e5a"),
    "ADMIN": ("admin@crisisos.app", "Cs!adf8646b7937"),
}

# Pre-iteration-5 hard-coded passwords — must now be REJECTED (SEC-001).
OLD_PASSWORDS = {
    "CITIZEN": "Citizen!2026",
    "RESPONDER": "Responder!2026",
    "OPERATOR": "Operator!2026",
    "ADMIN": "Admin!2026",
}


def ws_url(token: str) -> str:
    """Authenticated WS URL (SEC-003: JWT via ?token= query param)."""
    return f"{WS_URL}?token={token}"


@pytest.fixture(scope="session")
def api_client():
    """Unauthenticated JSON session — add Authorization headers per call."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def admin_token(api_client):
    """Admin JWT — needed for the now admin-only demo/reset (SEC-002)."""
    email, password = CREDENTIALS["ADMIN"]
    resp = api_client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"admin login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session", autouse=True)
def reset_demo(api_client, admin_token):
    """Reset demo data once before the suite for a clean state (admin-only)."""
    resp = api_client.post(f"{API}/demo/reset", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "reset"
    yield


@pytest.fixture(scope="session")
def tokens(api_client, reset_demo):
    """JWT access tokens for all four seeded roles."""
    out = {}
    for role, (email, password) in CREDENTIALS.items():
        resp = api_client.post(f"{API}/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200, f"login failed for {role}: {resp.text}"
        out[role] = resp.json()["access_token"]
    return out


@pytest.fixture(scope="session")
def auth(tokens):
    """auth('OPERATOR') -> Authorization header dict for that role."""
    def _for(role: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {tokens[role]}"}
    return _for
