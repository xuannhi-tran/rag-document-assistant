"""Two visitors must never see each other's documents or retrieve each other's chunks."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import func

from app import config
from app.models import Chunk, Document
from app.services.cleanup import purge_expired
from helpers import fake_embedding, make_pdf, new_session_headers

A_TEXT = "Alpha resume. Zebra migration specialist with expertise in savanna logistics."
B_TEXT = "Beta contract. Quantum espresso machine lease agreement for the downtown cafe."


@pytest.fixture(autouse=True)
def fake_models():
    """No sentence-transformers download and no Gemini calls."""
    with patch("app.services.ingestion.generate_embeddings_batch",
               side_effect=lambda texts: [fake_embedding(t) for t in texts]), \
         patch("app.services.retrieval.generate_embedding", side_effect=fake_embedding), \
         patch("app.services.ingestion.generate_document_summary",
               side_effect=lambda text: "Summary of the document that starts with: " + text[:25]):
        yield


def upload(client, headers, text, name):
    return client.post(
        "/upload/", headers=headers,
        files={"file": (name, make_pdf(text), "application/pdf")},
    )


def ask(client, headers, question, **extra):
    """Returns (response, list-of-context-chunks-sent-to-the-model)."""
    seen = []

    def fake_answer(q, chunks):
        seen.extend(chunks)
        return "stub answer"

    with patch("app.routes.ask.generate_answer", side_effect=fake_answer):
        res = client.post("/ask", headers=headers, json={"question": question, **extra})
    return res, seen


def test_sessions_cannot_retrieve_each_others_content(client):
    a, b = new_session_headers(), new_session_headers()
    ra = upload(client, a, A_TEXT, "alpha.pdf")
    rb = upload(client, b, B_TEXT, "beta.pdf")
    assert ra.status_code == 200 and rb.status_code == 200
    a_doc, b_doc = ra.json()["document_id"], rb.json()["document_id"]

    # Same query from both sessions, aimed at the *other* session's content
    res_a, ctx_a = ask(client, a, "Tell me about the quantum espresso machine and the zebra migration")
    res_b, ctx_b = ask(client, b, "Tell me about the quantum espresso machine and the zebra migration")
    assert res_a.status_code == 200 and res_b.status_code == 200
    assert ctx_a and ctx_b
    assert all("espresso" not in c.lower() and "beta.pdf" not in c for c in ctx_a)
    assert all("zebra" not in c.lower() and "alpha.pdf" not in c for c in ctx_b)
    assert any("zebra" in c.lower() for c in ctx_a)
    assert any("espresso" in c.lower() for c in ctx_b)

    # Supplying the other session's document id/name must not widen scope
    res, ctx = ask(client, a, "espresso machine lease", document_id=b_doc, document_ids=[b_doc],
                   document_names=["beta.pdf"])
    assert res.status_code == 200
    assert all("espresso" not in c.lower() for c in ctx)
    assert all(f"Document: beta.pdf" not in c for c in ctx)
    assert a_doc != b_doc


def test_summary_is_scoped_to_session(client):
    a, b = new_session_headers(), new_session_headers()
    upload(client, a, A_TEXT, "alpha.pdf")
    upload(client, b, B_TEXT, "beta.pdf")

    res, _ = ask(client, a, "Can you provide a comprehensive summary of the uploaded document?")
    assert res.json()["is_summary"] is True
    assert "Alpha" in res.json()["answer"] and "Beta" not in res.json()["answer"]

    res, _ = ask(client, b, "Can you provide a comprehensive summary of the uploaded document?")
    assert "Beta" in res.json()["answer"] and "Alpha" not in res.json()["answer"]


def test_session_without_uploads_gets_upload_first_and_no_model_call(client):
    other = new_session_headers()
    upload(client, other, A_TEXT, "alpha.pdf")  # data exists in the DB, but not for us
    empty = new_session_headers()

    with patch("app.routes.ask.generate_answer") as gen, \
         patch("app.routes.ask.retrieve_chunks") as retrieve, \
         patch("app.routes.ask.generate_document_summary") as summ:
        for q in ["Can you provide a comprehensive summary of the uploaded document?",
                  "What does the zebra migration specialist do?"]:
            res = client.post("/ask", headers=empty, json={"question": q})
            assert res.status_code == 200
            body = res.json()
            assert body["needs_upload"] is True
            assert "Upload a PDF first" in body["answer"]
        gen.assert_not_called()
        retrieve.assert_not_called()
        summ.assert_not_called()


def test_document_list_is_per_session(client):
    a, b, c = new_session_headers(), new_session_headers(), new_session_headers()
    upload(client, a, A_TEXT, "alpha.pdf")
    upload(client, b, B_TEXT, "beta.pdf")

    assert [d["filename"] for d in client.get("/documents", headers=a).json()["documents"]] == ["alpha.pdf"]
    assert [d["filename"] for d in client.get("/documents", headers=b).json()["documents"]] == ["beta.pdf"]
    assert client.get("/documents", headers=c).json()["documents"] == []


def test_cannot_delete_another_sessions_document(client, db_session):
    a, b = new_session_headers(), new_session_headers()
    b_doc = upload(client, b, B_TEXT, "beta.pdf").json()["document_id"]

    assert client.delete(f"/documents/{b_doc}", headers=a).status_code == 404
    assert db_session.query(Document).filter(Document.id == b_doc).count() == 1

    # Clearing session A must not touch B
    upload(client, a, A_TEXT, "alpha.pdf")
    assert client.delete("/documents", headers=a).json() == {"deleted": 1}
    assert [d["filename"] for d in client.get("/documents", headers=b).json()["documents"]] == ["beta.pdf"]

    # Owner can delete; chunks go with it
    assert client.delete(f"/documents/{b_doc}", headers=b).status_code == 200
    db_session.expire_all()
    assert db_session.query(Chunk).filter(Chunk.document_id == b_doc).count() == 0


def test_session_header_required_and_validated(client):
    assert client.get("/documents").status_code == 400
    assert client.get("/documents", headers={"X-Session-Id": "not-a-uuid"}).status_code == 400
    assert client.post("/ask", json={"question": "hi"}).status_code == 400
    assert client.post("/upload/", files={"file": ("a.pdf", make_pdf("x"), "application/pdf")}).status_code == 400


def test_upload_limits(client, monkeypatch):
    h = new_session_headers()
    monkeypatch.setattr(config, "MAX_FILES_PER_SESSION", 2)
    assert upload(client, h, A_TEXT, "one.pdf").status_code == 200
    assert upload(client, h, B_TEXT, "two.pdf").status_code == 200
    third = upload(client, h, "third", "three.pdf")
    assert third.status_code == 409
    # another session is unaffected by this session's quota
    assert upload(client, new_session_headers(), "fresh", "x.pdf").status_code == 200

    monkeypatch.setattr(config, "MAX_FILE_BYTES", 100)
    assert upload(client, new_session_headers(), A_TEXT, "big.pdf").status_code == 413

    monkeypatch.setattr(config, "MAX_FILE_BYTES", 10 * 1024 * 1024)
    bad = client.post("/upload/", headers=new_session_headers(),
                      files={"file": ("fake.pdf", b"not a pdf at all", "application/pdf")})
    assert bad.status_code == 400
    txt = client.post("/upload/", headers=new_session_headers(),
                      files={"file": ("notes.txt", b"%PDF-1.4", "text/plain")})
    assert txt.status_code == 400


def test_ask_rate_limit(client, monkeypatch):
    h = new_session_headers()
    upload(client, h, A_TEXT, "alpha.pdf")
    monkeypatch.setattr(config, "ASK_PER_MINUTE_SESSION", 3)
    codes = [ask(client, h, "zebra")[0].status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    # a different session is not throttled by the first one's budget
    h2 = new_session_headers()
    upload(client, h2, B_TEXT, "beta.pdf")
    assert ask(client, h2, "espresso")[0].status_code == 200


def test_purge_expired_removes_old_session_rows_only(client, db_session):
    h = new_session_headers()
    old_id = upload(client, h, A_TEXT, "old.pdf").json()["document_id"]
    new_id = upload(client, new_session_headers(), B_TEXT, "new.pdf").json()["document_id"]

    db_session.query(Document).filter(Document.id == old_id).update(
        {"upload_date": func.now() - timedelta(hours=config.RETENTION_HOURS + 1)}
    )
    legacy = Document(filename="legacy.pdf", content_type="application/pdf", session_id=None,
                      upload_date=func.now() - timedelta(days=30))
    db_session.add(legacy)
    db_session.commit()
    legacy_id = legacy.id

    assert purge_expired(db_session) == 1
    ids = {d.id for d in db_session.query(Document).all()}
    assert old_id not in ids and new_id in ids and legacy_id in ids  # legacy left for manual purge
    assert db_session.query(Chunk).filter(Chunk.document_id == old_id).count() == 0


def test_legacy_rows_are_invisible_to_every_session(client, db_session):
    """Rows uploaded before this change (session_id NULL) must never be retrievable."""
    doc = Document(filename="old_resume.pdf", content_type="application/pdf", summary="Legacy resume summary " * 5)
    db_session.add(doc)
    db_session.commit()
    db_session.add(Chunk(document_id=doc.id, content="legacy resume content",
                         embedding=fake_embedding("legacy resume content")))
    db_session.commit()

    h = new_session_headers()
    res, ctx = ask(client, h, "Can you provide a comprehensive summary of the uploaded document?")
    assert res.json()["needs_upload"] is True
    assert client.get("/documents", headers=h).json()["documents"] == []
    upload(client, h, B_TEXT, "beta.pdf")
    _, ctx = ask(client, h, "legacy resume content")
    assert all("legacy" not in c.lower() for c in ctx)
