# Documents Hub

A Django backend that receives uploaded documents, extracts their text content (direct extraction for born-digital files, OCR as a fallback for scanned content), and indexes it in Elasticsearch for full-text search.

> This is the server half of a two-service system. A companion Java scanner service (folder watching + upload) is planned as a separate component.

## Architecture

```
                    HTTP upload (JWT)
   Client   ─────────────────────────▶  Django API
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │ PostgreSQL  │  (Document metadata/status)
                                      └─────────────┘
                                             │
                                             ▼
                                      ┌─────────────┐
                                      │   Celery    │  (extraction pipeline)
                                      └──────┬──────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        ▼                    ▼                    ▼
                 direct text            OCR (Tesseract)      (unsupported
                 extraction             images + scanned      types →
                 (pdfplumber,           PDFs                  rejected)
                 python-docx,
                 odfpy, plain read)
                        │                    │
                        └────────────────────┴────────────────────┘
                                             ▼
                                      ┌───────────────┐
                                      │ Elasticsearch │  (searchable content)
                                      └───────────────┘
```

## Why Postgres *and* Elasticsearch

Postgres is the system of record for **metadata and status** (`Document.status`, timestamps, error messages) — the things you query relationally ("show me all failed uploads from today"). Elasticsearch is the system of record for **searchable content** — the extracted full text. Keeping these separate means a search-relevance change (e.g. a new analyzer) never requires a Postgres migration, and a Postgres schema change never requires reindexing.

## How to run it

```bash
cp documents-hub/.env.example documents-hub/.env
docker compose up --build
```

This starts Django (`:8000`), a Celery worker, PostgreSQL, Redis, and Elasticsearch (`:9200`).

**A note on Elasticsearch's version**: this project pins Elasticsearch `8.19.0`, deliberately not `9.x`. Elasticsearch 9.4+ requires a CPU with AVX2 instruction support — on hardware without it (some older CPUs, some virtualized/cloud environments with restricted CPU feature exposure), the container fails to start entirely with `The current machine does not support all of the following CPU features...`. Staying on 8.x avoids this hard requirement.

## Authentication

Endpoints (except `/search`) require a JWT access token, via `djangorestframework-simplejwt`.

**1. Create a user** (e.g. via Django admin at `/admin/`, or `python manage.py createsuperuser`).

**2. Obtain a token:**
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "123456"}'
# => {"access": "...", "refresh": "..."}
```

**3. Use it:**
```bash
curl http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer <access_token>"
```

`GET /api/documents/search` is intentionally left open (`AllowAny`) — see Known Limitations for the reasoning and its current gap.

## API reference

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/token/` | none | Obtain JWT access + refresh tokens |
| `POST` | `/api/token/refresh/` | none | Refresh an access token |
| `POST` | `/api/documents/upload` | JWT | Upload a document (multipart: `file`) |
| `GET` | `/api/documents/?status=` | JWT | List documents, optionally filtered by status |
| `GET` | `/api/documents/{id}` | JWT | Document metadata + status |
| `GET` | `/api/documents/search?q=` | none | Full-text search across all indexed documents |
| `/admin/` | | Django superuser | Browse/manage documents via Django admin |

### Example: upload a document

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@invoice.pdf"
```

### Example: search

```bash
curl "http://localhost:8000/api/documents/search?q=invoice+total"
```

## The extraction pipeline

For each uploaded file, `documents/extraction/pipeline.py` decides how to get text out of it, based on MIME type detected from file **content** (`python-magic`), not the filename extension:

| MIME type | Method | Library |
|---|---|---|
| `text/plain` | Direct read | built-in |
| Word (`.docx`, legacy `.doc`) | Direct extraction | `python-docx` |
| OpenDocument Text (`.odt`) | Direct extraction | `odfpy` |
| PDF with a text layer | Direct extraction | `pdfplumber` |
| PDF with no usable text layer (scanned) | OCR fallback | `pdf2image` + `pytesseract` |
| Images (`image/*`) | OCR | `pytesseract` |
| Anything else | Rejected (`UnsupportedDocumentError`) | — |

**Why direct extraction is tried before OCR for PDFs**: OCR is slower and introduces recognition errors; a PDF that already has a real text layer (the vast majority of "born-digital" PDFs) should just have that text read directly.

## Design decisions

- **Checksum-based dedup, server-side.** Uploading the same file content twice returns the existing `Document` record instead of creating a duplicate, regardless of what the uploading client does or doesn't track locally.
- **Direct text extraction before OCR, not the other way round**, for the accuracy/speed reasons above.
- **Permanent vs. transient failure handling** via a dedicated `PermanentDocumentError`, rather than by inspecting the *type* of exception a library happens to raise. An unsupported file type is permanent (retrying won't add support for it); a transient infra issue (e.g. a filesystem hiccup) is retried via `autoretry_for` + exponential backoff with jitter.
- **JWT authentication for the documents API, but `search` stays open.** These have different trust models — searching is read-only and meant for any authorized viewer of the documentation portal, while upload/management actions are gated behind a real account. See Known Limitations for what's still missing here.
- **Elasticsearch pinned to 8.19.0.** See "How to run it" above — 9.x has a hard AVX2 CPU requirement that isn't met on all development/deployment hardware.
- **No Prometheus/Grafana here.** A metrics/dashboard stack earns its place when a system has real operational dynamics worth watching live (queue depth, retry rates, throughput). This project's key states — extraction success/failure, which method was used, dedup hits — are already fully visible through `Document.status` and Django admin; a metrics dashboard wouldn't surface anything the database doesn't already show directly. Added observability tooling only where it answers a real question, not by default.

## Known limitations

- **`search` has no authentication or authorization at all.** Fine for a single-user/portfolio deployment, but in a real multi-tenant deployment this would need to at least require *some* authenticated session, even if more permissive than the upload endpoints.
- **Document storage is local disk** (`DOCUMENT_STORAGE_DIR`) — doesn't scale horizontally; multiple Django/Celery instances would need shared storage (S3, etc.) instead.
- **No OCR image pre-processing** (deskew, contrast enhancement) — OCR accuracy depends entirely on scan quality as-is.
- **No virus/malware scanning** on uploaded files.
- **`requirements.txt` is a full `pip freeze` output** (many transitive dependencies pinned individually) rather than a curated top-level list of direct dependencies — works correctly, but is harder to read at a glance and harder to intentionally upgrade one package at a time.
- **`SECRET_KEY` has no fallback default** — if `DJANGO_SECRET_KEY` isn't set in the environment, Django will fail to start rather than silently running insecurely. This is arguably a feature (fails loud, not quiet), but worth knowing before deploying without a `.env` in place.

## What I'd change at scale

- Move file storage to S3-compatible object storage.
- Add authentication (even lightweight) to the search endpoint.
- Add a dead-letter queue for permanently failed Celery tasks, so they can be inspected/replayed independently of just a DB status flag.
- Scope the Docker build context to `documents-hub/` specifically, rather than the whole repo root, to keep the image lean and avoid accidentally including unrelated files.
- Curate `requirements.txt` down to direct dependencies (see Known Limitations).

## Running tests locally

```bash
pip install -r requirements.txt
python manage.py test
```

Tests cover the extraction pipeline (using real sample files of each supported type in `documents/tests/`), the Celery task's permanent-vs-transient failure handling, serializers, JWT-authenticated views, and Elasticsearch indexing/search (a real integration test against a live Elasticsearch instance, not mocked).

Note: `test_elastic.py` requires a reachable Elasticsearch instance to pass (either via `docker compose up -d elasticsearch`, or your own local instance) — it's a genuine integration test, not a unit test with a mocked client.
