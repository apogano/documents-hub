import docx
import pdfplumber
from odf.opendocument import load
from odf.text import P
from odf import teletype

def extract_pdf_text_directly(file_path: str) -> str:
    """
    Attempts to read the existing text layer of a PDF directly, without
    OCR. Works for "born-digital" PDFs (reports, invoices, exports) that
    already contain real text -- fast and perfectly accurate, unlike OCR.

    Returns an empty string if no meaningful text layer exists (e.g. a
    scanned/image-only PDF) -- the caller is responsible for falling back
    to OCR in that case; this function does not do that itself, so it
    stays a simple, single-purpose function.
    """
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_docx_text(file_path: str) -> str:
    document = docx.Document(file_path)
    return "\n".join(paragraph.text for paragraph in document.paragraphs)
    
def extract_odt_text(file_path: str) -> str:
    document = load(file_path)
    paragraphs = document.getElementsByType(P)
    return "\n".join(teletype.extractText(p) for p in paragraphs)


def extract_txt_text(file_path:str) -> str:
    with open(file_path, "r", encoding="utf-8") as document:
        return "\n".join(document.readlines())
