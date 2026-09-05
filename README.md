# RAG Document Assistant API

A multilingual FastAPI backend for uploading PDF documents and asking questions about their contents. The service uses Retrieval-Augmented Generation (RAG): it retrieves semantically relevant document chunks from PostgreSQL/pgvector, then supplies them to Gemini to generate an answer grounded in the uploaded documents.

> This repository contains the backend API. The frontend is deployed separately.

## Features

- Upload PDF documents through a REST API
- Extract text from PDFs with `pypdf`
- Create overlapping text chunks for retrieval
- Generate 384-dimensional multilingual embeddings using `paraphrase-multilingual-MiniLM-L12-v2`
- Store documents, chunks, summaries and embeddings in PostgreSQL with `pgvector`
- Retrieve the 12 nearest chunks using cosine distance
- Generate multilingual answers and structured document summaries with Google Gemini
- Search within one selected document, multiple selected documents, or the full collection
- Health-check endpoint and automated tests using a separate pgvector database
- Docker Compose configuration and GitHub Actions test workflow

## RAG pipeline

1. `POST /upload/` accepts a PDF.
2. The backend extracts its text, generates a structured summary, and splits the text into overlapping chunks.
3. The summary and chunks are embedded with the multilingual SentenceTransformers model and stored in PostgreSQL/pgvector.
4. `POST /ask` embeds the question, finds the closest chunks by cosine distance, and sends the retrieved context with the question to Gemini.
5. Gemini returns an answer in the same language as the question.

## Tech stack

| Area | Technology |
| --- | --- |
| API | Python 3.12, FastAPI, Uvicorn |
| PDF processing | pypdf |
| Embeddings | sentence-transformers, `paraphrase-multilingual-MiniLM-L12-v2` |
| Vector database | PostgreSQL 16, pgvector, SQLAlchemy |
| Generative model | Google Gemini (`gemini-flash-lite-latest`) |
| Testing | pytest, FastAPI TestClient |
| Containers / CI | Docker, Docker Compose, GitHub Actions |

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Check database connectivity |
| `POST` | `/upload/` | Upload and index a PDF |
| `POST` | `/ask` | Ask a question about uploaded documents |

### Upload a document

```bash
curl -X POST http://localhost:8000/upload/ \
  -F "file=@/path/to/document.pdf"
```

The response includes the generated `document_id`, which can be used to restrict later questions to that document.

### Ask a question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarise this document", "document_id": 1}'
```

`/ask` also accepts `document_ids`, `filename`, and `document_names` for choosing the search scope.

## Run with Docker Compose

### Prerequisites

- Docker and Docker Compose
- A Gemini API key

### 1. Configure environment variables

Create a `.env` file at the repository root:

```env
GEMINI_API_KEY=your_gemini_api_key
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=choose_a_local_password
POSTGRES_DB=ragdb
TEST_POSTGRES_USER=rag_test_user
TEST_POSTGRES_PASSWORD=choose_a_different_test_password
TEST_POSTGRES_DB=ragdb_test
TEST_DATABASE_URL=postgresql://rag_test_user:choose_a_different_test_password@localhost:5433/ragdb_test
```

Start from `.env.example`; it also documents the optional `CORS_ORIGINS` setting. `DATABASE_URL` is assembled for the API container by `docker-compose.yml`.

### 2. Start the API and database

```bash
docker compose up --build
```

On a fresh database, initialise the pgvector extension and tables before uploading a document:

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS vector;"'
docker compose exec web python -m app.create_tables
```

The API is exposed at `http://localhost:8000` and its interactive OpenAPI documentation is at `http://localhost:8000/docs`.

## Run tests

Start the PostgreSQL test service first:

```bash
docker compose up -d test-db
```

Then run the test suite in an environment configured with a test database URL:

```bash
pytest
```

The GitHub Actions workflow provisions a separate `pgvector/pgvector:pg16` test database and runs the same test suite on pushes and pull requests to `main`.

## Project structure

```text
.
├── routes/                 # Health, upload and question-answer endpoints
├── services/               # PDF extraction, chunking, embeddings, retrieval and LLM calls
├── tests/                  # API tests and PDF fixture
├── database.py             # SQLAlchemy engine and sessions
├── models.py               # Document and vector-backed Chunk models
├── schemas.py              # Request schema for /ask
├── create_tables.py        # Schema creation / summary-column migration
├── docker-compose.yml
└── Dockerfile
```

## Security and configuration notes

- Keep `GEMINI_API_KEY` only in `.env` locally or in the deployment platform's secret manager. Never commit it.
- Restrict CORS to the local and deployed frontend origins that need access.
- Apply upload size limits and sanitise uploaded filenames before a public deployment.
- Use a distinct database and credentials for production, development and tests.

## Future improvements

- Return page-level citations and source passages with every answer
- Add OCR support for scanned PDFs
- Add authentication and document-level access control
- Use hybrid retrieval and reranking to improve retrieval quality
- Evaluate retrieval and generation with a labelled benchmark set
- Support asynchronous ingestion and progress updates for large files

## License

This project is intended for educational and portfolio purposes.
