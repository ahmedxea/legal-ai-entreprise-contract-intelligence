"""
Test fixtures for Phase 1 tests.

Strategy:
  - API tests use FastAPI's TestClient (synchronous, no real HTTP).
  - The production SQLite DB is NOT touched. Each test session gets an
    isolated temporary database via the `tmp_db_path` fixture.
  - Storage service upload is patched to avoid filesystem side-effects.
  - document_processor.process is patched to a no-op so background
    extraction does not interfere with upload response-code assertions.
"""
import io
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Ensure backend/ is on sys.path when running `pytest` from backend/
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


# ── Minimal in-memory file factories ─────────────────────────────────────────

def make_pdf_bytes() -> bytes:
    """
    Return a small but structurally valid PDF (single page, one text line).
    Created with a raw byte string so the tests have no extra dependency.
    """
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Resources<</Font<</F1 4 0 R>>>>"
        b"/Contents 5 0 R"
        b">>endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"5 0 obj<</Length 44>>\nstream\n"
        b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET\n"
        b"endstream\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000266 00000 n \n"
        b"0000000347 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\n"
        b"startxref\n445\n%%EOF\n"
    )


def make_docx_bytes() -> bytes:
    """Return a minimal DOCX file with one paragraph."""
    from docx import Document

    doc = Document()
    doc.add_paragraph("This is a test contract paragraph.")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_client(tmp_path_factory):
    """
    Build a TestClient that:
      - uses an isolated temporary SQLite DB
      - stubs out the storage upload so no real files are written
      - stubs out document_processor.process so background extraction
        does not run (avoids file-not-found errors on fake blob URLs)
    """
    tmp_dir = tmp_path_factory.mktemp("test_db")
    db_path = str(tmp_dir / "test_contracts.db")
    uploads_path = str(tmp_dir / "uploads")

    # Patch storage upload before importing the app
    with (
        patch(
            "app.services.local_storage_service.LocalStorageService.__init__",
            lambda self, storage_path=uploads_path: (
                setattr(self, "storage_path", Path(uploads_path))
                or Path(uploads_path).mkdir(parents=True, exist_ok=True)
                or None
            ),
        ),
        patch(
            "app.services.sqlite_service.DatabaseService.__init__",
            lambda self, db_path=db_path: (
                setattr(self, "db_path", db_path)
                or Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                or None
            ),
        ),
    ):
        pass  # imports handled below without these patches active

    # Import after path is set
    from app.services.sqlite_service import DatabaseService as _DB
    test_db = _DB(db_path=db_path)

    from main import app
    from fastapi.testclient import TestClient

    # Patch module-level db_service in contracts router + document_processor
    from app.services.storage_quota_service import storage_quota_service as _quota_svc
    original_quota_db = _quota_svc._db
    _quota_svc._db = test_db

    with (
        patch("app.api.contracts.db_service", test_db),
        patch("app.services.document_processor.DocumentProcessorService._db", test_db),
        patch(
            "app.services.storage_factory.storage.upload_file",
            new_callable=AsyncMock,
            return_value="/fake/path/contract.pdf",
        ),
        patch(
            "app.services.document_processor.document_processor.process",
            new_callable=AsyncMock,
        ),
    ):
        client = TestClient(app)
        yield client

    _quota_svc._db = original_quota_db
