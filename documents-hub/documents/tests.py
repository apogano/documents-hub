from django.test import TestCase 
import os
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
        
