import pytesseract
from pdf2image import convert_from_path
from PIL import Image


def run_ocr_on_image(file_path: str) -> str:
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)

def run_ocr_on_pdf(file_path: str) -> str:
    """
    Used as the fallback when a PDF has no usable text layer (i.e. it's a
    scanned document saved as PDF). Converts each page to an image first,
    since Tesseract works on images, not PDF pages directly.
    """
    pages = convert_from_path(file_path)
    text_parts = [pytesseract.image_to_string(page) for page in pages]
    return "\n".join(text_parts)
