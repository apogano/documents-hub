from django.test import TestCase 
import os
from django.utils import timezone
from django.conf import settings

from elasticsearch import Elasticsearch
from documents.search import (
    get_es_client, 
    ensure_index_exists,
    index_document,
    search_documents
)


class ElasticTestCase(TestCase): 
    def test_get_client(self):
        self.assertIsInstance(
            get_es_client(),
            Elasticsearch
        )
        
    def test_ensure_index_exists(self):
        ensure_index_exists()   

    def test_index_and_search_document(self):
        index_document(
            document_id="test-doc-1",
            filename="invoice_march.pdf",
            content="This invoice covers services rendered in March, total amount due is 450 dollars.",
            mime_type="application/pdf",
            uploaded_at=timezone.now(),  
        )
        results = search_documents("invoice total")
        self.assertEqual(
            results,
            [{'document_id': 'test-doc-1', 'filename': 'invoice_march.pdf', 'score': 0.5753642, 'snippet': 'This invoice covers services rendered in March, total amount due is 450 dollars.'}]
        )
        
        
        
        
