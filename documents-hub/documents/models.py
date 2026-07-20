from django.db import models
import uuid

class DocumentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"

class ExtractionMethod(models.TextChoices):
    DIRECT_TEXT = "direct_text", "Direct text extraction"
    OCR = "ocr", "OCR"


class Document(models.Model):
    """
    Represents the uploaded document and its processing state.
    
    The extracted full text itself will NOT stored here -- it will be in ElasticSearch.
    This table is the system of record for *metadata and status*; 
    ElasticSearch will be the system of record for *searchable content*.
    """
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    original_filename = models.CharField(max_length=512)
    file_path = models.CharField(max_length=1024)
    checksum = models.CharField(max_length=64, unique=True,db_index=True)
    mime_type = models.CharField(max_length=128)
    status = models.CharField(
        max_length=16,
        choices=DocumentStatus.choices,
        default=DocumentStatus.PENDING,
    ) 
    extraction_method = models.CharField(
        max_length=16,
        choices=ExtractionMethod.choices,
        null=True,
        blank=True,
    )
    error_message = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.original_filename} ({self.status})"
