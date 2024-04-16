import datetime as dt
import time
import signal

from scheduler import Scheduler

import nesis.api.core.tasks.document_management as document_management
import nesis.api.core.util.http as http
import logging

_LOG = logging.getLogger(__name__)

_terminate = False


def stop(signum, frame):
    global _terminate
    _terminate = True


def start(config: dict, http_client: http.HttpClient) -> None:
    global _terminate

    _LOG.info("Running manager...")

    entry_point_lookup = {"fetch_documents": document_management.ingest_documents}

    scheduler: Scheduler = Scheduler()
    tasks = config.get("tasks") or {}
    job_count = 0
    for task in tasks.keys():
        task_config = tasks.get(task)
        if task_config is None or not task_config.get("enabled", True):
            continue
        interval = task_config.get("schedule")
        if interval:
            _LOG.info(f"Setting up scheduled task {task} at interval {interval}")
            scheduler.cyclic(
                dt.timedelta(minutes=interval),
                entry_point_lookup[task],
                kwargs={"http_client": http_client, "config": config},
            )
            job_count += 1
        else:
            _LOG.info(f"Setting up scheduled task {task} to run once")
            scheduler.once(
                dt.timedelta(),
                entry_point_lookup[task],
                kwargs={"http_client": http_client, "config": config},
            )
            job_count += 1

    try:
        while job_count > 0 and not _terminate:
            scheduler.exec_jobs()
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        _LOG.info(f"Terminating {__name__} process")
