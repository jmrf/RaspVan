import logging
import signal
import time
import warnings
from functools import wraps
from typing import Callable

import numpy as np
from funcy import chunks
from tqdm import tqdm

from common.utils.exec import run_in_event_loop
from common.utils.exec import run_sync


logger = logging.getLogger(__name__)


def deprecated(func: Callable) -> Callable:
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""

    @wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter("always", DeprecationWarning)  # turn off filter
        warnings.warn(
            f"Call to deprecated function '{func.__name__}'.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        warnings.simplefilter("default", DeprecationWarning)  # reset filter
        return func(*args, **kwargs)

    return new_func


def batched(batch_size, p_bar=True):
    def wrapper(func):
        @wraps(func)
        def batcher(long_list, *args, **kwargs):

            _iter = chunks(batch_size, long_list)
            if p_bar:
                _iter = tqdm(_iter, total=len(long_list))

            results = []
            for chunk in _iter:
                res = func(chunk, *args, **kwargs)
                if res:
                    results.extend(res)

            return results

        return batcher

    return wrapper


def timeit(func: Callable) -> Callable:
    @wraps(func)
    def timed_wrapper(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        delta = time.time() - start
        logger.debug(f"function '{func.__name__}' took {delta:.4f}")  # type: ignore
        return res

    return timed_wrapper


def fire_and_forget(f: Callable) -> Callable:
    @wraps(f)
    def wrapped(*args, **kwargs):
        return run_in_event_loop(f, args, kwargs)

    return wrapped


def force_sync(fn):
    """Turns an async function into sync"""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        return run_sync(fn, *args, **kwargs)

    return wrapper


def f_timeout(timeout_secs: int):
    def wrapper(func):
        @wraps(func)
        def time_limited(*args, **kwargs):
            # Register an handler for the timeout
            def handler(signum, frame):
                raise Exception(f"Timeout for function '{func.__name__}'")

            # Register the signal function handler
            signal.signal(signal.SIGALRM, handler)

            # Define a timeout for your function
            signal.alarm(timeout_secs)

            result = None
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                raise exc
            finally:
                # disable the signal alarm
                signal.alarm(0)

            return result

        return time_limited

    return wrapper


def as_numpy_array(func, dtype=np.float32):
    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        r = func(self, *args, **kwargs)
        r_type = type(r).__name__
        if r_type in {"ndarray", "EagerTensor", "Tensor", "list"}:
            return np.array(r, dtype)
        else:
            raise TypeError("unrecognized type {}: {}".format(r_type, type(r)))

    return arg_wrapper


def as_numpy_batch(func, dtype=np.float32):
    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        r = func(self, *args, **kwargs)
        r_type = type(r).__name__
        if r_type in {"ndarray", "EagerTensor", "Tensor", "list"}:
            r = np.array(r, dtype)
        else:
            raise TypeError("unrecognized type {}: {}".format(r_type, type(r)))

        if r.ndim < 2:
            r = np.expand_dims(r, axis=0)
        return r

    return arg_wrapper
