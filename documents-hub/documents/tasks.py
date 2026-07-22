import logging
from django.core.exceptions import ValidationError

from celery import shared_task
from django.utils import timezone

from .extraction.pipeline import UnsupportedDocumentError, extract_content
from .models import Document,DocumentStatus
from .search import index_document

logger = logging.getLogger(__name__)

class PermanentDocumentError(Exception):
    """
    Raised for failures that retrying will never fix: unsupported file
    types, corrupt files that can't be opened at all, etc. Deciding
    permanence explicitly here -- rather than by inspecting the *type* of
    exception a library happens to raise -- matters because libraries like
    Pillow or pdfplumber can raise the same exception type (e.g. OSError)
    for both truly transient issues (a disk hiccup) and permanent ones (a
    corrupt file). Branching on exception type conflates those two very
    different situations; branching on an explicit decision does not.
    """

    
    
@shared_task(
    bind=True,
    autoretry_for=(OSError,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
)
def process_document(self, document_id: str):
    try:
        document = Document.objects.get(id=document_id)
    except (Document.DoesNotExist, ValidationError):
        logger.error("Document %s not found, skipping", document_id)
        return

    document.status = DocumentStatus.PROCESSING
    document.save(update_fields=["status"])

    try:
        try:
            text, method = extract_content(document.file_path, document.mime_type)
        except UnsupportedDocumentError as exc:
            raise PermanentDocumentError(str(exc))

        index_document(
            document_id=str(document.id),
            filename=document.original_filename,
            content=text,
            mime_type=document.mime_type,
            uploaded_at=document.uploaded_at,
        )

        document.status = DocumentStatus.SUCCEEDED
        document.extraction_method = method
        document.processed_at = timezone.now()
        document.save(update_fields=["status", "extraction_method", "processed_at"])

    except PermanentDocumentError as exc:
        document.status = DocumentStatus.FAILED
        document.error_message = str(exc)
        document.processed_at = timezone.now()
        document.save(update_fields=["status", "error_message", "processed_at"])
        logger.warning("Document %s failed permanently: %s", document_id, exc)

    except OSError as exc:
        is_final_attempt = self.request.retries >= self.max_retries
        document.status = DocumentStatus.FAILED if is_final_attempt else DocumentStatus.PROCESSING
        document.error_message = str(exc)
        document.save(update_fields=["status", "error_message"])
        logger.exception(
            "Document %s failed on attempt %s/%s%s",
            document_id,
            self.request.retries + 1,
            self.max_retries + 1,
            " (final attempt)" if is_final_attempt else " (will retry)",
        )
        raise

    except Exception as exc:  # noqa: BLE001 - unexpected: treat as permanent
        document.status = DocumentStatus.FAILED
        document.error_message = str(exc)
        document.processed_at = timezone.now()
        document.save(update_fields=["status", "error_message", "processed_at"])
        logger.exception("Document %s failed on unexpected error", document_id)
        raise
