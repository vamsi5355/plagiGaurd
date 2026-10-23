from fastapi.testclient import TestClient

from plagiguard.api import app


def test_health_metadata_and_analysis():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").status_code == 200
    response = client.post("/analyze", json={"suspicious_text": "same text", "source_text": "same text"})
    assert response.status_code == 200
    assert response.json()["label"] in {"plagiarism", "original"}


def test_file_analysis_rejects_unsupported_format():
    client = TestClient(app)
    response = client.post(
        "/analyze-file",
        files={
            "suspicious": ("a.pdf", b"not supported", "application/pdf"),
            "source": ("b.txt", b"source", "text/plain"),
        },
    )
    assert response.status_code == 400
