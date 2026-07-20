from django.test import TestCase 

from .models import Document 
from .extraction.mime_detect import detect_mime_type 
from .extraction.direct_text import (
    extract_txt_text,
    extract_docx_text,
    extract_odt_text,
    extract_pdf_text_directly
)

class DocumentTestCase(TestCase): 
    def test_detect_mime_type(self): 
        self.assertEqual(  
            detect_mime_type('/tmp/uploads/documents/test.txt'),
            'text/plain') 
        
        self.assertEqual(  
            detect_mime_type('/tmp/uploads/documents/TestDocxDocument.docx'),
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
         
        self.assertEqual(  
            detect_mime_type('/tmp/uploads/documents/TestODtDocument.odt'),
            'application/vnd.oasis.opendocument.text') 
        
        self.assertEqual(  
            detect_mime_type('/tmp/uploads/documents/TestPDFDocument.pdf'),
            'application/pdf') 
            
    
    def test_direct_text(self): 
        self.assertEqual( 
            extract_txt_text('/tmp/uploads/documents/test.txt'),
            'This is a test txt document. \n\ntest1\n\ntest2\n' ) 
        
        self.assertEqual( 
            extract_docx_text('/tmp/uploads/documents/TestDocxDocument.docx'),
            'This is a test docx document. \ntest1\ntest2') 
        
        self.assertEqual( 
            extract_odt_text('/tmp/uploads/documents/TestODtDocument.odt'),
            'This is a test odt document. \ntest1\ntest2') 
            
        self.assertEqual( 
            extract_pdf_text_directly('/tmp/uploads/documents/TestPDFDocument.pdf'),
            'This is a test pdf document.\ntest1\ntest2') 
