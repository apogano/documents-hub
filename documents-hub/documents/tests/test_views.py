from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


from documents.models import Document, DocumentStatus


User = get_user_model()


class ListDocumentsViewTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="admin",
            password="123456",
        )

        refresh = RefreshToken.for_user(self.user)

        self.access_token = str(
            refresh.access_token
        )

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

        self.url = reverse("list-documents")

    def authenticate(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )


    def test_list_documents_requires_authentication(self):
        response = self.client.get(
            self.url
        )

        self.assertEqual(
            response.status_code,
            401,
        )


    def test_authenticated_user_can_list_documents(self):
        self.authenticate()

        response = self.client.get(
            self.url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["original_filename"],
            "test.pdf",
        )


    def test_list_documents_can_filter_by_status(self):
        Document.objects.create(
            original_filename="failed.pdf",
            checksum="xyz789",
            mime_type="application/pdf",
            status=DocumentStatus.FAILED,
            error_message="bad file",
            uploaded_at=timezone.now(),
        )

        self.authenticate()

        response = self.client.get(
            self.url,
            {
                "status": DocumentStatus.FAILED,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["status"],
            DocumentStatus.FAILED,
        )


    def test_list_documents_returns_expected_fields(self):
        self.authenticate()

        response = self.client.get(
            self.url
        )

        document = response.data[0]

        expected_fields = {
            "id",
            "original_filename",
            "checksum",
            "mime_type",
            "status",
            "extraction_method",
            "error_message",
            "uploaded_at",
            "processed_at",
        }

        self.assertEqual(
            set(document.keys()),
            expected_fields,
        )
