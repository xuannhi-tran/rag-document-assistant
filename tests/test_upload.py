from pathlib import Path

def test_upload(client):
    # Define the path to the sample PDF file
    sample_pdf_path = Path(__file__).parent / "fixtures" / "sample.pdf"
    
    # Open the sample PDF file
    with open(sample_pdf_path, "rb") as file_object:
        # Make a POST request to the upload endpoint
        response = client.post(
            "/upload/",
            files={"file": ("sample.pdf", file_object, "application/pdf")}
        )
    
    # Assert that the response status code is 200
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "sample.pdf"
    assert data["status"] == "processed"