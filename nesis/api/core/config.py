import os
from tzlocal import get_localzone

default = {
    "server": {
        "port": os.environ.get("NESIS_API_SERVER_PORT", "6000"),
        "address": os.environ.get("NESIS_API_SERVER_ADDRESS", "0.0.0.0"),
    },
    "database": {
        "url": os.environ.get("NESIS_API_DATABASE_URL"),
        "debug": os.environ.get("NESIS_API_DATABASE_DEBUG", False),
        "create": bool(os.environ.get("NESIS_API_DATABASE_CREATE", "false")),
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
        "executors": {"default_size": 30, "pool_size": 3},
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
    "apps": {
        "session": {"expiry": os.environ.get("NESIS_API_APPS_SESSION_EXPIRY") or 1800}
    },
}
