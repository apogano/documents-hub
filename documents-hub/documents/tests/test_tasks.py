from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase
from django.utils import timezone

from documents.models import Document, DocumentStatus
from documents.tasks import process_document
from documents.extraction.pipeline import UnsupportedDocumentError


class ProcessDocumentTaskTests(TestCase):

    def setUp(self):
        self.document = Document.objects.create(
            file_path="/tmp/test.pdf",
            mime_type="application/pdf",
            original_filename="test.pdf",
            uploaded_at=timezone.now(),
            status=DocumentStatus.PENDING,
        )

    @patch("documents.tasks.index_document")
    @patch("documents.tasks.extract_content")
    def test_process_document_success(
        self,
        mock_extract,
        mock_index,
    ):
        """
        Document is extracted, indexed, and marked as succeeded.
        """

        mock_extract.return_value = (
            "hello world",
            "pdf",
        )

        process_document(str(self.document.id))

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.status,
            DocumentStatus.SUCCEEDED,
        )

        self.assertEqual(
            self.document.extraction_method,
            "pdf",
        )

        self.assertIsNotNone(
            self.document.processed_at,
        )

        mock_extract.assert_called_once_with(
            self.document.file_path,
            self.document.mime_type,
        )

        mock_index.assert_called_once_with(
            document_id=str(self.document.id),
            filename=self.document.original_filename,
            content="hello world",
            mime_type=self.document.mime_type,
            uploaded_at=self.document.uploaded_at,
        )


    def test_process_document_missing_document(self):
        """
        Missing documents should be ignored.
        """

        process_document(str(uuid4()))

        # No exception expected


    @patch(
        "documents.tasks.extract_content",
        side_effect=UnsupportedDocumentError(
            "unsupported file type"
        ),
    )
    def test_process_document_unsupported_document(
        self,
        mock_extract,
    ):
        """
        Unsupported files are permanent failures.
        """

        process_document(str(self.document.id))

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.status,
            DocumentStatus.FAILED,
        )

        self.assertEqual(
            self.document.error_message,
            "unsupported file type",
        )

        self.assertIsNotNone(
            self.document.processed_at,
        )

        mock_extract.assert_called_once()


    @patch(
        "documents.tasks.extract_content",
        side_effect=OSError(
            "temporary filesystem failure"
        ),
    )
    def test_process_document_oserror_retry(
        self,
        mock_extract,
    ):
        """
        OSError should leave the document processing
        because Celery will retry.
        """

        with self.assertRaises(OSError):
            process_document(str(self.document.id))

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.status,
            DocumentStatus.PROCESSING,
        )

        self.assertEqual(
            self.document.error_message,
            "temporary filesystem failure",
        )


    @patch(
        "documents.tasks.extract_content",
        side_effect=ValueError(
            "unexpected parser crash"
        ),
    )
    def test_process_document_unexpected_error(
        self,
        mock_extract,
    ):
        """
        Unexpected exceptions are marked failed.
        """

        with self.assertRaises(ValueError):
            process_document(str(self.document.id))

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.status,
            DocumentStatus.FAILED,
        )

        self.assertEqual(
            self.document.error_message,
            "unexpected parser crash",
        )

        self.assertIsNotNone(
            self.document.processed_at,
        )
