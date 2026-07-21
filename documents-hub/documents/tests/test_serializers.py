from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from documents.models import Document, DocumentStatus
from documents.serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
)


class DocumentSerializerTests(TestCase):

    def setUp(self):
        self.document = Document.objects.create(
            original_filename="test.pdf",
            checksum="abc123",
            mime_type="application/pdf",
            status=DocumentStatus.SUCCEEDED,
            extraction_method="pdf",
            error_message="",
            uploaded_at=timezone.now(),
            processed_at=timezone.now(),
        )

    def test_document_serializer_contains_expected_fields(self):
        serializer = DocumentSerializer(self.document)

        data = serializer.data

        self.assertEqual(
            data["original_filename"],
            "test.pdf",
        )

        self.assertEqual(
            data["checksum"],
            "abc123",
        )

        self.assertEqual(
            data["mime_type"],
            "application/pdf",
        )

        self.assertIn("status", data)
        self.assertIn("uploaded_at", data)
        self.assertIn("processed_at", data)


    def test_document_serializer_fields_are_read_only(self):
        serializer = DocumentSerializer(
            data={
                "original_filename": "changed.pdf",
                "checksum": "newchecksum",
                "status": DocumentStatus.FAILED,
            }
        )

        self.assertTrue(serializer.is_valid())

        # ModelSerializer ignores read-only fields during creation
        self.assertNotIn(
            "status",
            serializer.validated_data,
        )


class DocumentUploadSerializerTests(TestCase):

    def test_upload_serializer_accepts_file(self):
        uploaded_file = SimpleUploadedFile(
            "test.pdf",
            b"fake pdf content",
            content_type="application/pdf",
        )

        serializer = DocumentUploadSerializer(
            data={
                "file": uploaded_file,
            }
        )

        self.assertTrue(serializer.is_valid())

        self.assertIn(
            "file",
            serializer.validated_data,
        )


    def test_upload_serializer_requires_file(self):
        serializer = DocumentUploadSerializer(
            data={}
        )

        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "file",
            serializer.errors,
        )


    def test_upload_serializer_rejects_invalid_file_object(self):
        serializer = DocumentUploadSerializer(
            data={
                "file": "not-a-file",
            }
        )

        self.assertFalse(serializer.is_valid())

        self.assertIn(
            "file",
            serializer.errors,
        )
