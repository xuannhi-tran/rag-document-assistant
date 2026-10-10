from pathlib import Path
from unittest.mock import patch

from helpers import new_session_headers


def test_upload(client):
    sample_pdf_path = Path(__file__).parent / "fixtures" / "sample.pdf"

    # Gemini and embeddings are mocked so the test doesn't call live services
    with (
        patch(
            "app.services.ingestion.generate_document_summary",
            return_value="Test summary",
        ),
        patch(
            "app.services.ingestion.generate_embeddings_batch",
            side_effect=lambda texts: [[0.0] * 384 for _ in texts],
        ),
    ):
        with open(sample_pdf_path, "rb") as file_object:
            response = client.post(
                "/upload/",
                files={"file": ("sample.pdf", file_object, "application/pdf")},
                headers=new_session_headers(),
            )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "sample.pdf"
    assert data["status"] == "processed"