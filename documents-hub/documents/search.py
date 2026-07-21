from django.conf import settings
from elasticsearch import Elasticsearch

_client = None

def get_es_client() -> Elasticsearch:
    """
    Lazily creates a single shared Elasticsearch client. Lazy so that
    importing this module (e.g. during Django startup or tests) doesn't
    require Elasticsearch to already be reachable.
    """
    global _client
    if _client is None:
        _client = Elasticsearch(settings.ELASTICSEARCH_URL)
    return _client


def ensure_index_exists():
    client = get_es_client()
    if not client.indices.exists(index=settings.ELASTICSEARCH_INDEX):
        client.indices.create(
            index = settings.ELASTICSEARCH_INDEX,
            mappings = {
                "properties":{
                    "document_id":{"type":"keyword"},
                    "filename":{"type":"text"},
                    "content":{"type":"text"},
                    "mime_type":{"type":"keyword"},
                    "uploaded_at":{"type":"date"}
                }
            },
        )


def index_document(document_id:str, filename:str,content:str,mime_type:str,uploaded_at):
    client = get_es_client()
    ensure_index_exists()
    client.index(
        index = settings.ELASTICSEARCH_INDEX,
        id = document_id,
        document = {
            "document_id": document_id,
            "filename": filename,
            "content": content,
            "mime_type": mime_type,
            "uploaded_at": uploaded_at.isoformat(timespec="milliseconds") if uploaded_at else None,
        },
    )


def search_documents(query:str,limit: int=20):
    client = get_es_client()
    ensure_index_exists()
    response = client.search(
        index = settings.ELASTICSEARCH_INDEX,
        query = {
            "multi_match": {
                "query": query,
                "fields": ["content","filename^2"], # filename matches weighted higher
            }
        },
        size = limit
    )
    return [
        {
            "document_id": hit["_source"]["document_id"],
            "filename": hit["_source"]["filename"],
            "score": hit["_score"],
            "snippet": hit["_source"]["content"][:300],
        }
        for hit in response["hits"]["hits"]
    ]
