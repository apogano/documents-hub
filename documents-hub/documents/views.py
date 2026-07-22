import hashlib
import os

from django.conf import settings
from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Document, DocumentStatus
from .serializers import DocumentSerializer,DocumentUploadSerializer

from .extraction.mime_detect import detect_mime_type
from .tasks import process_document

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_documents(request):
    status_filter = request.query_params.get("status")
    queryset = Document.objects.all()
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    return Response(DocumentSerializer(queryset, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def document_details(request, document_id):
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(DocumentSerializer(document).data)


def _calculate_checksum(file_obj) -> str:
    hasher = hashlib.sha256()
    for chunk in file_obj.chunks():
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_document(request):
    """
    Ingests one document from an authenticated scanner client.

    Checksum calculation happens here too (server-side), as a second layer on
    top of whatever calculation the folder scanner service already does client-side --
    protects against the case where the scanner's local state was lost
    (e.g. redeployed/reset) but the server already has this exact file.
    """
    serializer = DocumentUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    uploaded_file = serializer.validated_data["file"]

    checksum = _calculate_checksum(uploaded_file)

    existing = Document.objects.filter(checksum=checksum).first()
    if existing:
        return Response(DocumentSerializer(existing).data, status=status.HTTP_200_OK)

    os.makedirs(settings.DOCUMENT_STORAGE_DIR, exist_ok=True)
    stored_filename = f"{checksum}_{uploaded_file.name}"
    stored_path = os.path.join(settings.DOCUMENT_STORAGE_DIR, stored_filename)
    with open(stored_path, "wb") as dest:
        for chunk in uploaded_file.chunks():
            dest.write(chunk)

    mime_type = detect_mime_type(stored_path)

    document = Document.objects.create(
        original_filename=uploaded_file.name,
        file_path=stored_path,
        checksum=checksum,
        mime_type=mime_type,
        status=DocumentStatus.PENDING,
    )

    process_document.delay(str(document.id))

    return Response(DocumentSerializer(document).data, status=status.HTTP_202_ACCEPTED)
