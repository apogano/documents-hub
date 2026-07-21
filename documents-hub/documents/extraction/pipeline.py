from django.conf import settings

from .direct_text import (
    extract_txt_text,
    extract_docx_text,
    extract_odt_text,
    extract_pdf_text_directly
)
from .ocr import run_ocr_on_image, run_ocr_on_pdf

from .mime_detect import WORD_MIME_TYPES,ODT_MIME_TYPES


class UnsupportedDocumentError(Exception):
    """Raised for MIME types this pipeline doesn't know how to handle."""


def extract_content(file_path: str, mime_type: str) -> tuple[str, str]:
    """
    Returns (extracted_text, extraction_method).

    Direct text extraction is always tried before OCR for PDFs, since OCR
    is slower and introduces recognition errors that direct extraction
    doesn't have. OCR is only used when there's genuinely no text layer to
    read (a scanned/image-only PDF), or for image files where there was
    never a text layer to begin with.
    """
    if mime_type == "text/plain":
        return extract_txt_text(file_path), "direct_text"
    
    if mime_type in WORD_MIME_TYPES:
        return extract_docx_text(file_path), "direct_text"
        
    if mime_type in ODT_MIME_TYPES:
        return extract_odt_text(file_path), "direct_text"          
            
    if mime_type == "application/pdf":
        text = extract_pdf_text_directly(file_path)
        if text and len(text.strip()) >= settings.MIN_MEANINGFUL_TEXT_LENGTH:
            return text, "direct_text"
        # No usable text layer -- this is a scanned PDF, fall back to OCR.
        return run_ocr_on_pdf(file_path), "ocr"

    if mime_type.startswith("image/"):
        return run_ocr_on_image(file_path), "ocr"

    raise UnsupportedDocumentError(f"Unsupported mime type: {mime_type}")
