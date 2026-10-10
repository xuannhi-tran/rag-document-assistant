from pathlib import Path
from unittest.mock import patch

from helpers import new_session_headers


def test_ask_endpoint(client):
    sample_pdf_path = Path(__file__).parent / "fixtures" / "sample.pdf"
    headers = new_session_headers()

    # Step 1: Upload a sample PDF file (Gemini and embeddings mocked)
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
        with open(sample_pdf_path, "rb") as pdf_file:
            response = client.post(
                "/upload/",
                files={"file": ("sample.pdf", pdf_file, "application/pdf")},
                headers=headers,
            )

    assert response.status_code == 200

    # Step 2: Ask a question with the same session id
    with (
        patch(
            "app.services.retrieval.generate_embedding",
            return_value=[0.0] * 384,
        ),
        patch("app.routes.ask.generate_answer", return_value="random answer"),
    ):
        response = client.post(
            "/ask",
            json={"question": "What is the content of the sample PDF?"},
            headers=headers,
        )

    # Step 3: Assert the response
    assert response.status_code == 200
    assert response.json()["answer"] == "random answer"