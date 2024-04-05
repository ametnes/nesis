import multiprocessing as mp
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
IOBoundPool = ThreadPoolExecutor(mp.cpu_count() * 20)
