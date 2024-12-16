import logging
import time
from datetime import datetime as dt
from typing import Any, Callable
from typing import Dict

import coloredlogs
from apscheduler.schedulers.background import BackgroundScheduler

from raspvan.workers.relay import RelayClient

logger = logging.getLogger(__name__)
coloredlogs.install(logger=logger, level=logging.DEBUG)


class LightTimer:
    def __init__(self):
        self.pending_task = {}
        self.sched = BackgroundScheduler(daemon=True)
        self.sched.start()

    def _scheduled_run(self, _id, func, kwargs):
        func(**kwargs)
        self.sched.remove_job(_id)
        del self.pending_task[_id]

    @staticmethod
    def _make_schedule_id(func, f_kwargs, delay):
        now = dt.now().isoformat()
        args_str = "-".join(f"{k}={v}" for k, v in f_kwargs.items())
        return f"{now}-[{func.__name__}-({args_str})]-delay->{delay}"

    def get(self):
        return [
            (
                j.next_run_time.isoformat(),
                self.pending_task[j.id],
            )
            for j in self.sched.get_jobs()
        ]

    def put(self, delay: int, func: Callable, f_kwargs: Dict[str, Any]):
        try:
            job_id = self._make_schedule_id(func, f_kwargs, delay)
            logger.info(f"New schedule -> {job_id}")

            self.pending_task[job_id] = {"f": func.__name__, **f_kwargs}
            self.sched.add_job(
                self._scheduled_run,
                "interval",
                seconds=delay,
                id=job_id,
                args=(job_id, func, f_kwargs),
            )
        except Exception as e:
            logger.exception(f"Error in PUT schedule: {e}")
            logger.exception(e)


if __name__ == "__main__":
    relays = RelayClient()

    tdelay = 0.75
    lt = LightTimer()
    for i, channel in enumerate([1, 2, 3, 4]):
        t = i * tdelay + tdelay
        lt.put(
            delay=t, func=relays.switch, f_kwargs={"mode": True, "channels": [channel]}
        )

    for i, channel in enumerate([4, 3, 2, 1]):
        t = i * tdelay + tdelay
        lt.put(
            delay=3 + t,
            func=relays.switch,
            f_kwargs={"mode": False, "channels": [channel]},
        )

    pending = lt.get()
    while pending:
        try:
            pending = lt.get()
            time.sleep(0.5)
        except KeyboardInterrupt:
            break
