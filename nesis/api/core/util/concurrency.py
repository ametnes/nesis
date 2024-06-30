import multiprocessing as mp
import os
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
