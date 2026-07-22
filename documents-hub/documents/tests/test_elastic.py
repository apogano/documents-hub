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
        # Elasticsearch data isn't covered by Django's test-transaction
        # rollback (that only applies to the DB), so clean up explicitly --
        # otherwise this document persists in a real, shared ES index
        # across test runs.
        self.addCleanup(
            lambda: get_es_client().delete(
                index=settings.ELASTICSEARCH_INDEX, id="test-doc-1", ignore=[404]
            )
        )
       
        index_document(
            document_id="test-doc-1",
            filename="invoice_march.pdf",
            content="This invoice covers services rendered in March, total amount due is 450 dollars.",
            mime_type="application/pdf",
            uploaded_at=timezone.now(),  
        )
        # Elasticsearch needs a moment to make a newly-indexed document
        # searchable (near-real-time, not immediate) -- refresh forces it
        # to be visible before we search, avoiding a flaky race.
        get_es_client().indices.refresh(index=settings.ELASTICSEARCH_INDEX)

        results = search_documents("invoice total")
        
        # Exact relevance-score assertions are brittle -- BM25 scores can
        # shift slightly between ES versions or depending on what else is
        # in the index. Check what actually matters instead: the right
        # document came back, with a positive relevance score.
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["document_id"], "test-doc-1")
        self.assertEqual(results[0]["filename"], "invoice_march.pdf")
        self.assertGreater(results[0]["score"], 0)

        
        
        
        
