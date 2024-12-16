import signal
from contextlib import contextmanager
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll


@contextmanager
def timeout(duration: int):
    def timeout_handler(signum, frame):
        raise RuntimeError(f"Block timed out after {duration} seconds")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(duration)
    try:
        yield
    finally:
        signal.alarm(0)


@contextmanager
def no_alsa_err():
    def _py_error_handler(filename, line, function, err, fmt):
        pass

    error_handler_func = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
    c_error_handler = error_handler_func(_py_error_handler)

    asound = cdll.LoadLibrary("libasound.so")
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)
