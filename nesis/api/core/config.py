import os

default = {
    "database": {
        "url": os.environ.get("NESIS_API_DATABASE_URL"),
        "debug": False,
        "create": False,
    },
    "tasks": {"fetch_documents": {"schedule": 5, "enabled": True}},
    "rag": {
        "endpoint": os.environ.get("NESIS_API_RAG_ENDPOINT", "http://localhost:8080")
    },
    "memcache": {
        "hosts": [os.environ.get("NESIS_MEMCACHE_HOSTS", "127.0.0.1:11211")],
        "session": {"expiry": 0},
        "cache": {
            "timeout_default": 300,
        },
    },
}
