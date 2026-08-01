from unittest.mock import patch
from app.main import app
from pathlib import Path



def test_ask_endpoint(client):
    sample_pdf_path = Path(__file__).parent / "fixtures" / "sample.pdf"
    # Step 1: Upload a sample PDF file
    with open(sample_pdf_path,"rb") as pdf_file:
        response = client.post("/upload/", files={"file": pdf_file})
    assert response.status_code == 200

    # Step 2: Mock the generate_answer function
    with patch("app.routes.ask.generate_answer") as mock_generate:
        mock_generate.return_value = "random answer"

        # Step 3: Call the /ask endpoint with a question
        response = client.post("/ask", json={"question": "What is the content of the sample PDF?"})
        
        # Step 4: Assert the response
        assert response.status_code == 200
        assert response.json()["answer"] == "random answer"