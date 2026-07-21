import magic

WORD_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
}

ODT_MIME_TYPES = {
    'application/vnd.oasis.opendocument.text'
}

def detect_mime_type(file_path: str) -> str:
    """
    Detects MIME type from file *content*, not the filename extension.
    A renamed .txt-as-.pdf should be caught here, not trusted blindly --
    extensions are user/scanner-supplied metadata, not verified fact.
    """
    return magic.from_file(file_path, mime=True)
