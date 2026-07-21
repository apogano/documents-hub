from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Document
from .serializers import DocumentSerializer


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
