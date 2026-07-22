FROM python:3.12-slim

WORKDIR /code

# tesseract-ocr: the OCR engine itself (pytesseract is just a Python wrapper around it)
# poppler-utils: needed by pdf2image to rasterize PDF pages for OCR
# libmagic1: needed by python-magic for content-based MIME detection
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev tesseract-ocr poppler-utils libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt  .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
