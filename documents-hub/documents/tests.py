from django.test import TestCase 
import os
from django.utils import timezone
from django.conf import settings

from .models import Document 
from .extraction.mime_detect import detect_mime_type 
from .extraction.direct_text import (
    extract_txt_text,
    extract_docx_text,
    extract_odt_text,
    extract_pdf_text_directly
)
from .extraction.ocr import run_ocr_on_image, run_ocr_on_pdf

from .extraction.pipeline import extract_content

from elasticsearch import Elasticsearch
from .search import (
    get_es_client, 
    ensure_index_exists,
    index_document,
    search_documents
)

class DocumentTestCase(TestCase): 
    def test_detect_mime_type(self): 
        self.assertEqual(  
            detect_mime_type(
            os.path.join(settings.BASE_DIR, 'documents/tests/TestTxtDocument.txt')),
            'text/plain') 
        
        self.assertEqual(  
            detect_mime_type(os.path.join(settings.BASE_DIR, 'documents/tests/TestDocxDocument.docx')),
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
         
        self.assertEqual(  
            detect_mime_type(os.path.join(settings.BASE_DIR, 'documents/tests/TestODtDocument.odt')),
            'application/vnd.oasis.opendocument.text') 
        
        self.assertEqual(  
            detect_mime_type(os.path.join(settings.BASE_DIR, 'documents/tests/TestPDFDocument.pdf')),
            'application/pdf') 
            
        self.assertEqual(  
            detect_mime_type(os.path.join(settings.BASE_DIR, 'documents/tests/TestImageDocument.png')),
            'image/png')             
            
    
    def test_direct_text(self): 
        self.assertEqual( 
            extract_txt_text(os.path.join(settings.BASE_DIR, 'documents/tests/TestTxtDocument.txt')),
            'This is a test txt document.\n\ntest1\n\ntest2\n' ) 
        
        self.assertEqual( 
            extract_docx_text(os.path.join(settings.BASE_DIR, 'documents/tests/TestDocxDocument.docx')),
            'This is a test docx document.\ntest1\ntest2') 
        
        self.assertEqual( 
            extract_odt_text(os.path.join(settings.BASE_DIR, 'documents/tests/TestODtDocument.odt')),
            'This is a test odt document.\ntest1\ntest2') 
            
        self.assertEqual( 
            extract_pdf_text_directly(os.path.join(settings.BASE_DIR, 'documents/tests/TestPDFDocument.pdf')),
            'This is a test pdf document.\ntest1\ntest2') 

    def test_ocr(self):
        self.assertEqual( 
            run_ocr_on_image(os.path.join(settings.BASE_DIR, 'documents/tests/TestImageDocument.png')),
            'This is a test png document.\ntestl\ntest2\n') 
        
        self.assertEqual( 
            run_ocr_on_pdf(os.path.join(settings.BASE_DIR, 'documents/tests/TestPDFImageDocument.pdf')),
            'This is a test pdf image document.\ntestl\n\ntest\n')         
        
    def test_pipeline_text(self):
        filename = os.path.join(settings.BASE_DIR, 'documents/tests/TestTxtDocument.txt')
        self.assertEqual( 
            extract_content(
                filename,
                detect_mime_type(filename)
            ),
            ('This is a test txt document.\n\ntest1\n\ntest2\n','direct_text') 
        ) 
        
    def test_pipeline_docx(self):
        filename = os.path.join(settings.BASE_DIR, 'documents/tests/TestDocxDocument.docx')
        self.assertEqual( 
            extract_content(
                filename,
                detect_mime_type(filename)
            ),
            ('This is a test docx document.\ntest1\ntest2','direct_text') 
        )         

    def test_pipeline_odt(self):
        filename = os.path.join(settings.BASE_DIR, 'documents/tests/TestODtDocument.odt')
        self.assertEqual( 
            extract_content(
                filename,
                detect_mime_type(filename)
            ),
            ('This is a test odt document.\ntest1\ntest2','direct_text') 
        )          
        
    def test_pipeline_pdf(self):
        #DIRECT_TEXT
        filename = os.path.join(settings.BASE_DIR, 'documents/tests/TestPDFDocument.pdf')
        self.assertEqual( 
            extract_content(
                filename,
                detect_mime_type(filename)
            ),
            ('This is a test pdf document.\ntest1\ntest2','direct_text') 
        )
        #OCR
        filename = os.path.join(settings.BASE_DIR, 'documents/tests/TestPDFImageDocument.pdf')
        self.assertEqual( 
            extract_content(
                filename,
                detect_mime_type(filename)
            ),
            ('This is a test pdf image document.\ntestl\n\ntest\n','ocr') 
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
        print(results)
