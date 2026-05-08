from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import app  # noqa: E402


client = TestClient(app)


def test_scored_endpoint_respects_size_band_and_sub_industry() -> None:
    response = client.get(
        "/api/companies/scored",
        params={"size_band": "smb", "sub_industry": "AI Infrastructure"},
    )

    assert response.status_code == 200
    rows = response.json()
    assert rows
    assert all(30 <= row["employee_count"] <= 200 for row in rows)
    assert all(row["sub_industry"] == "AI Infrastructure" for row in rows)


def test_export_csv_uses_same_filters_as_table() -> None:
    response = client.get(
        "/api/export.csv",
        params={"min_score": 80, "sub_industry": "AI Infrastructure", "size_band": "smb"},
    )

    assert response.status_code == 200
    body = response.text
    assert "company_name,domain,industry,sub_industry" in body
    assert "AI Infrastructure" in body
