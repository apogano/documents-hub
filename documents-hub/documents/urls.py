from django.urls import path

from documents import views

urlpatterns = [
    path("", views.list_documents, name="list-documents"),
    path("<uuid:document_id>", views.document_details, name="document-details"),
    path("upload", views.upload_document, name="upload-document"),
    path("search", views.search, name="search"),
]
