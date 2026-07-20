from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    list_display = (
        "original_filename",
        "mime_type",
        "status",
    )

    search_fields = (
        "original_filename",
        "file_path",
    )

    list_filter = (
        "mime_type",
        "status",
    )
