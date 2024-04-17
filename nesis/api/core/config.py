import os
from tzlocal import get_localzone

default = {
    "database": {
        "url": os.environ.get("NESIS_API_DATABASE_URL"),
        "debug": False,
        "create": False,
    },
    "tasks": {
        "job": {
            "stores": {"url": os.environ.get("NESIS_API_TASKS_JOB_STORES_URL")},
            "defaults": {
                "coalesce": True,
                "max_instances": 3,
                "misfire_grace_time": 60,
            },
        },
        "timezone": os.environ.get("NESIS_API_TASKS_TIMEZONE", str(get_localzone())),
    },
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
