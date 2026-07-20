from django.test import TestCase

from .models import Document
from .extraction.mime_detect import detect_mime_type


class DocumentTestCase(TestCase):

    def test_detect_mime_type(self):
        self.assertEqual(  detect_mime_type('/tmp/uploads/documents/test.txt'),'text/plain')
        self.assertEqual(  detect_mime_type('/tmp/uploads/documents/TestDocxDocument.docx'),'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        self.assertEqual(  detect_mime_type('/tmp/uploads/documents/TestODtDocument.odt'),'application/vnd.oasis.opendocument.text')
        self.assertEqual(  detect_mime_type('/tmp/uploads/documents/TestPDFDocument.pdf'),'application/pdf')
