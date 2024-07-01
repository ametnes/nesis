import multiprocessing as mp
import os
import queue
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    TimeoutError,
    as_completed,
    wait,
    ALL_COMPLETED,
)

# A CPU bound thread pool
CPUBoundPool = ProcessPoolExecutor(mp.cpu_count() + 2)

# An IO bound thread pool
IOBoundPool = ThreadPoolExecutor(
    os.environ.get("NESIS_API_WORKER_POOL_SIZE") or mp.cpu_count() * 5
)


class BlockingThreadPoolExecutor(ThreadPoolExecutor):
    def __init__(self, *, queue_size=0, **kwargs):
        super().__init__(**kwargs)
        self._work_queue = queue.Queue(maxsize=queue_size)
