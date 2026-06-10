"""
Unit tests for the /logs router.
"""

from fastapi.testclient import TestClient


class TestCreateLog:
    """POST /logs — create emission log entries."""

    def test_create_valid_log(self, client: TestClient):
        """Happy path: valid log entry is created with correct CO₂e."""
        response = client.post("/logs", json={
            "category": "transport",
            "sub_type": "car_petrol",
            "quantity": 100,
            "note": "Commute to office",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "transport"
        assert data["sub_type"] == "car_petrol"
        assert data["quantity"] == 100
        assert data["unit"] == "km"
        # 100 km × 0.171 kg/km = 17.1 kg CO₂e
        assert data["co2e_kg"] == 17.1
        assert data["note"] == "Commute to office"
        assert data["id"] is not None

    def test_create_diet_log(self, client: TestClient):
        """Diet log calculates correctly."""
        response = client.post("/logs", json={
            "category": "diet",
            "sub_type": "beef_meal",
            "quantity": 2,
        })
        assert response.status_code == 201
        data = response.json()
        # 2 meals × 3.0 kg/meal = 6.0 kg
        assert data["co2e_kg"] == 6.0
        assert data["unit"] == "meal"

    def test_create_log_invalid_category(self, client: TestClient):
        """Invalid category returns 422."""
        response = client.post("/logs", json={
            "category": "invalid",
            "sub_type": "car_petrol",
            "quantity": 10,
        })
        assert response.status_code == 422

    def test_create_log_invalid_sub_type(self, client: TestClient):
        """Sub_type that doesn't belong to the category returns 422."""
        response = client.post("/logs", json={
            "category": "transport",
            "sub_type": "beef_meal",
            "quantity": 10,
        })
        assert response.status_code == 422

    def test_create_log_zero_quantity(self, client: TestClient):
        """Zero quantity is rejected (must be > 0)."""
        response = client.post("/logs", json={
            "category": "transport",
            "sub_type": "car_petrol",
            "quantity": 0,
        })
        assert response.status_code == 422

    def test_create_log_negative_quantity(self, client: TestClient):
        """Negative quantity is rejected."""
        response = client.post("/logs", json={
            "category": "transport",
            "sub_type": "car_petrol",
            "quantity": -5,
        })
        assert response.status_code == 422


class TestListLogs:
    """GET /logs — retrieve recent emission logs."""

    def test_list_logs_empty(self, client: TestClient):
        """No logs returns empty list."""
        response = client.get("/logs")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_logs_returns_created(self, client: TestClient):
        """Created logs appear in the list."""
        client.post("/logs", json={
            "category": "energy",
            "sub_type": "electricity_grid",
            "quantity": 50,
        })
        client.post("/logs", json={
            "category": "diet",
            "sub_type": "vegan_meal",
            "quantity": 3,
        })

        response = client.get("/logs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestDeleteLog:
    """DELETE /logs/{id} — remove a log entry."""

    def test_delete_existing_log(self, client: TestClient):
        """Successfully delete a log entry."""
        create_resp = client.post("/logs", json={
            "category": "shopping",
            "sub_type": "clothing_item",
            "quantity": 1,
        })
        log_id = create_resp.json()["id"]

        delete_resp = client.delete(f"/logs/{log_id}")
        assert delete_resp.status_code == 204

        # Verify it's gone
        list_resp = client.get("/logs")
        assert len(list_resp.json()) == 0

    def test_delete_nonexistent_log(self, client: TestClient):
        """Deleting a non-existent log returns 404."""
        response = client.delete("/logs/999")
        assert response.status_code == 404


class TestLogsSummary:
    """GET /logs/summary — aggregated CO₂e breakdown."""

    def test_summary_with_logs(self, client: TestClient):
        """Summary aggregates correctly by category."""
        client.post("/logs", json={
            "category": "transport",
            "sub_type": "car_petrol",
            "quantity": 100,
        })
        client.post("/logs", json={
            "category": "transport",
            "sub_type": "bus",
            "quantity": 50,
        })
        client.post("/logs", json={
            "category": "diet",
            "sub_type": "beef_meal",
            "quantity": 1,
        })

        response = client.get("/logs/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["entry_count"] == 3
        assert data["total_co2e_kg"] > 0
        assert "transport" in data["by_category"]
        assert "diet" in data["by_category"]
