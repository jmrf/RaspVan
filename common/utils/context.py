import signal
from contextlib import contextmanager


@contextmanager
def timeout(duration: int):
    def timeout_handler(signum, frame):
        raise Exception(f"Block timed out after {duration} seconds")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(duration)
    try:
        yield
    finally:
        signal.alarm(0)
