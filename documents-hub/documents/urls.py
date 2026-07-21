from django.urls import path

from documents import views

urlpatterns = [
    path("", views.list_documents, name="list-documents"),
]
