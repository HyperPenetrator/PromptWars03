"""
Unit tests for the /goals router.
"""

from datetime import date, timedelta

from fastapi.testclient import TestClient


class TestCreateGoal:
    """POST /goals — create reduction goals."""

    def test_create_valid_goal(self, client: TestClient):
        """Happy path: goal is created with 0% initial progress."""
        deadline = (date.today() + timedelta(days=30)).isoformat()
        response = client.post("/goals", json={
            "category": "transport",
            "target_co2e_kg": 50.0,
            "deadline": deadline,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "transport"
        assert data["target_co2e_kg"] == 50.0
        assert data["current_co2e_kg"] == 0.0
        assert data["progress_pct"] == 0.0

    def test_create_goal_invalid_category(self, client: TestClient):
        """Invalid category returns 422."""
        deadline = (date.today() + timedelta(days=30)).isoformat()
        response = client.post("/goals", json={
            "category": "invalid",
            "target_co2e_kg": 50.0,
            "deadline": deadline,
        })
        assert response.status_code == 422


class TestGoalProgress:
    """Goal progress updates when logs are added."""

    def test_progress_updates_with_logs(self, client: TestClient):
        """Adding logs in the goal's category increases progress."""
        deadline = (date.today() + timedelta(days=30)).isoformat()

        # Create a transport goal: max 50 kg this month
        goal_resp = client.post("/goals", json={
            "category": "transport",
            "target_co2e_kg": 50.0,
            "deadline": deadline,
        })
        goal_id = goal_resp.json()["id"]

        # Log 100 km petrol driving = 17.1 kg CO₂e
        client.post("/logs", json={
            "category": "transport",
            "sub_type": "car_petrol",
            "quantity": 100,
        })

        # Check progress: 17.1 / 50 = 34.2%
        goals = client.get("/goals").json()
        goal = next(g for g in goals if g["id"] == goal_id)
        assert goal["current_co2e_kg"] == 17.1
        assert goal["progress_pct"] == 34.2

    def test_progress_ignores_other_categories(self, client: TestClient):
        """Logs in other categories don't affect this goal."""
        deadline = (date.today() + timedelta(days=30)).isoformat()

        client.post("/goals", json={
            "category": "diet",
            "target_co2e_kg": 20.0,
            "deadline": deadline,
        })

        # Log in transport (not diet)
        client.post("/logs", json={
            "category": "transport",
            "sub_type": "car_petrol",
            "quantity": 100,
        })

        goals = client.get("/goals").json()
        diet_goal = next(g for g in goals if g["category"] == "diet")
        assert diet_goal["current_co2e_kg"] == 0.0
        assert diet_goal["progress_pct"] == 0.0


class TestUpdateGoal:
    """PATCH /goals/{id} — update goal targets."""

    def test_update_target(self, client: TestClient):
        """Update the target CO₂e."""
        deadline = (date.today() + timedelta(days=30)).isoformat()
        create_resp = client.post("/goals", json={
            "category": "energy",
            "target_co2e_kg": 100.0,
            "deadline": deadline,
        })
        goal_id = create_resp.json()["id"]

        update_resp = client.patch(f"/goals/{goal_id}", json={
            "target_co2e_kg": 75.0,
        })
        assert update_resp.status_code == 200
        assert update_resp.json()["target_co2e_kg"] == 75.0

    def test_update_nonexistent_goal(self, client: TestClient):
        """Updating a non-existent goal returns 404."""
        response = client.patch("/goals/999", json={"target_co2e_kg": 50.0})
        assert response.status_code == 404

    def test_update_deadline(self, client: TestClient):
        """Update only the deadline of a goal."""
        deadline = (date.today() + timedelta(days=30)).isoformat()
        new_deadline = (date.today() + timedelta(days=60)).isoformat()
        create_resp = client.post("/goals", json={
            "category": "energy",
            "target_co2e_kg": 100.0,
            "deadline": deadline,
        })
        goal_id = create_resp.json()["id"]

        update_resp = client.patch(f"/goals/{goal_id}", json={
            "deadline": new_deadline,
        })
        assert update_resp.status_code == 200
        assert update_resp.json()["deadline"] == new_deadline


class TestDeleteGoal:
    """DELETE /goals/{id} — remove goals."""

    def test_delete_goal(self, client: TestClient):
        """Successfully delete a goal."""
        deadline = (date.today() + timedelta(days=30)).isoformat()
        create_resp = client.post("/goals", json={
            "category": "shopping",
            "target_co2e_kg": 30.0,
            "deadline": deadline,
        })
        goal_id = create_resp.json()["id"]

        delete_resp = client.delete(f"/goals/{goal_id}")
        assert delete_resp.status_code == 204

        goals = client.get("/goals").json()
        assert len(goals) == 0

    def test_delete_nonexistent_goal(self, client: TestClient):
        """Deleting a non-existent goal returns 404."""
        response = client.delete("/goals/999")
        assert response.status_code == 404
