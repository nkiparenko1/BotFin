"""Integration tests against running BotFin API."""

import uuid

import httpx
import pytest

BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "TestPass123!"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": "Test User"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestHealth:
    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestAuth:
    def test_me_endpoint(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == TEST_EMAIL
        assert data["profile"] is not None

    def test_login(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_duplicate_register(self, client):
        resp = client.post(
            "/api/auth/register",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": "Dup"},
        )
        assert resp.status_code == 400


class TestProfile:
    def test_onboarding(self, client, auth_headers):
        resp = client.post(
            "/api/profile/onboarding",
            headers=auth_headers,
            json={
                "step": 3,
                "data": {
                    "age": 30,
                    "monthly_income": 100000,
                    "fixed_expenses": 30000,
                    "variable_expenses": 20000,
                    "savings": 150000,
                    "main_goal": "apartment",
                    "goal_years": 5,
                },
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["health_score"] > 0
        assert data["plan"] is not None
        assert len(data["plan"]) == 3

    def test_get_profile(self, client, auth_headers):
        resp = client.get("/api/profile", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["health_score"] is not None


class TestBudget:
    def test_create_and_list_transactions(self, client, auth_headers):
        create = client.post(
            "/api/budget/transactions",
            headers=auth_headers,
            json={
                "amount": 1500.50,
                "category": "food",
                "date": "2025-06-01",
                "description": "Продукты",
            },
        )
        assert create.status_code == 200, create.text
        tx_id = create.json()["id"]

        listing = client.get("/api/budget/transactions", headers=auth_headers)
        assert listing.status_code == 200
        assert len(listing.json()) >= 1

        update = client.patch(
            f"/api/budget/transactions/{tx_id}",
            headers=auth_headers,
            json={"category": "transport"},
        )
        assert update.status_code == 200
        assert update.json()["category"] == "transport"

        delete = client.delete(f"/api/budget/transactions/{tx_id}", headers=auth_headers)
        assert delete.status_code == 204


class TestGoals:
    def test_create_goal(self, client, auth_headers):
        resp = client.post(
            "/api/goals",
            headers=auth_headers,
            json={
                "name": "Квартира",
                "target_amount": 3000000,
                "current_amount": 500000,
                "expected_return": 10,
                "deadline_months": 60,
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["calculations"]["monthly_deposit"] > 0
        assert data["calculations"]["progress_pct"] > 0

    def test_goal_limit(self, client, auth_headers):
        resp = client.post(
            "/api/goals",
            headers=auth_headers,
            json={
                "name": "Вторая цель",
                "target_amount": 100000,
                "current_amount": 0,
                "expected_return": 5,
                "deadline_months": 12,
            },
        )
        assert resp.status_code == 400


class TestTax:
    def test_tax_flow(self, client, auth_headers):
        save = client.post(
            "/api/tax/profile",
            headers=auth_headers,
            json={
                "bought_property": True,
                "property_amount": 2000000,
                "paid_education": True,
                "education_amount": 50000,
            },
        )
        assert save.status_code == 200, save.text

        calc = client.post("/api/tax/calculate", headers=auth_headers)
        assert calc.status_code == 200, calc.text
        data = calc.json()
        assert data["total_return"] > 0
        assert len(data["deductions"]) >= 1
        assert len(data["documents"]) >= 1
