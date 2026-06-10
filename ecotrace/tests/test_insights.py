"""
Unit tests for the /insights router.

Uses mocked Gemini responses to avoid API calls during testing.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

MOCK_INSIGHT = {
    "summary": "You drove 100 km this week, emitting 17.1 kg CO₂e.",
    "top_emission": {"category": "transport", "co2e_kg": 17.1, "percentage": 100},
    "suggestions": [
        {
            "action": "Switch 2 commute days to public transit",
            "potential_saving_kg": 8.2,
            "difficulty": "easy",
        },
    ],
    "encouragement": "Every kilometer on the bus is a step toward a greener commute!",
}


class TestInsights:
    """POST /insights — AI-powered emission insights."""

    @patch("routers.insights.generate_insight", return_value=MOCK_INSIGHT)
    def test_insights_with_logs(self, mock_gemini, client: TestClient):
        """Insights are generated from recent logs."""
        # Add some logs first
        client.post("/logs", json={
            "category": "transport",
            "sub_type": "car_petrol",
            "quantity": 100,
        })

        response = client.post("/insights?days=7")
        assert response.status_code == 200
        data = response.json()
        assert data["log_count"] == 1
        assert "insight" in data
        assert data["insight"]["summary"] is not None
        assert len(data["insight"]["suggestions"]) > 0

        # Verify Gemini was called
        mock_gemini.assert_called_once()

    @patch("routers.insights.generate_insight", return_value=MOCK_INSIGHT)
    def test_insights_empty_logs(self, mock_gemini, client: TestClient):
        """Insights work even with no logs (asks user to start tracking)."""
        response = client.post("/insights?days=7")
        assert response.status_code == 200
        data = response.json()
        assert data["log_count"] == 0

    @patch(
        "routers.insights.generate_insight",
        side_effect=RuntimeError("Gemini API timeout"),
    )
    def test_insights_gemini_failure(self, mock_gemini, client: TestClient):
        """Gemini failure returns 503."""
        response = client.post("/insights?days=7")
        assert response.status_code == 503


class TestWeeklySummary:
    """GET /insights/weekly — weekly comparison."""

    @patch("routers.insights.generate_insight", return_value=MOCK_INSIGHT)
    def test_weekly_summary(self, mock_gemini, client: TestClient):
        """Weekly summary includes this week's data."""
        client.post("/logs", json={
            "category": "diet",
            "sub_type": "beef_meal",
            "quantity": 3,
        })

        response = client.get("/insights/weekly")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "weekly"
        assert data["this_week_entries"] == 1
        assert data["this_week_co2e_kg"] > 0
