import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Text
from typing import Tuple
from typing import Union


def run_sync(fn, *args, **kwargs):
    res = fn(*args, **kwargs)
    if asyncio.iscoroutine(res):
        return asyncio.get_event_loop().run_until_complete(res)
    return res


async def async_parallel_exec(
    func_calls: List[Tuple[Union[Text, int], Callable, Tuple]],
    max_workers: int = 20,
    as_mapping: bool = True,
) -> Union[Dict[Any, Any], List[Any]]:
    """Calls a series of functions in parallel. Maps each result to the
    function key provided to return results in the same order as requested
    Args:
        func_calls (List[Tuple[Union[Text, int], Callable, Tuple[Any]]]):
            list of tuples; (function ID, function, function parameters)
        max_workers (int, optional): [description]. Defaults to 10.
    """

    def mapping_func_call(func_id, func, *args, **kwargs):
        return {func_id: func(*args, **kwargs)}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Initialize the event loop
        loop = asyncio.get_event_loop()

        # Create all tasks
        tasks = [
            loop.run_in_executor(
                executor, mapping_func_call, *tuple([f_id, func, *f_params])
            )
            for f_id, func, f_params in func_calls
        ]

        # Initializes the tasks to run and awaits their results
        res_map = {}
        for response in await asyncio.gather(*tasks):
            res_map.update(response)

    if as_mapping:
        return res_map
    else:
        # sort the results in the order they came in the requests
        f_keys = [f_id for f_id, _, _ in func_calls]
        return [res_map[fk] for fk in f_keys]


def parallel_exec(
    func_calls: List[Callable],
    func_params: List[Tuple],
    max_workers: int = 20,
):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        calls = []
        for (
            func,
            params,
        ) in zip(func_calls, func_params):
            calls.append(executor.submit(func, *params))

        results = [c.result() for c in calls]

    return results


def run_in_event_loop(f: Callable, args, kwargs):
    return asyncio.get_event_loop().run_in_executor(None, f, *args, *kwargs)
