import time
from collections.abc import Generator
from contextlib import contextmanager

from flask import current_app


@contextmanager
def benchmark(message: str) -> Generator:
    """Benchmark method useful for debugging slow stuff."""
    t1 = time.perf_counter()
    yield
    t2 = time.perf_counter()
    current_app.logger.debug(f"{message}, Time={t2 - t1}")
