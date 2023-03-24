import copy
import json
import logging
import time
from typing import List

import redis
from smbus2 import SMBus

logger = logging.getLogger(__name__)

MIN_CHANNEL = 1
MAX_CHANNEL = 4
DEVICE_ADDR = 0x27

# NOTE: Flip values accordingly to the relay wiring. i.e:
# connected in NO (normally open) => ON = True / OFF = False
# connected in NC (normally close) => ON = False / OFF = True
ON = False
OFF = True
OFF_STATE = [1] * 4

class RedisLightsMemory:
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.key = "lights_state"
        self.r = redis.Redis(host=redis_host, port=redis_port)
        self.r.ping()  # to raise exception if couldn't connect

    def set(self, state):
        self.r.set(self.key, json.dumps(state))

    def get(self):
        return json.loads(self.r.get(self.key))


class RelayClient:
    def __init__(self):
        self.state_store = RedisLightsMemory()
        if self.state_store.get() is None:
            self.state_store.set(OFF_STATE)

    @staticmethod
    def write_relay(value: int):
        with SMBus(1) as bus:
            bus.write_byte_data(DEVICE_ADDR, 0, value)

    @staticmethod
    def validate(channels, mode):
        if any([c < MIN_CHANNEL or c > MAX_CHANNEL for c in channels]):
            raise ValueError(f"Invalid channels: {channels}")

        if mode not in (0, 1):
            raise ValueError(f"Invalid mode: {mode}")

    def calc_state(self, channels, mode):
        new_state = copy.copy(self.state_store.get())
        # new_state[channel - 1] = mode ^ 1

        if isinstance(channels, int):
            channels = [channels]

        for c in channels:
            new_state[c - 1] = mode ^ 1  # flip state

        mask = "".join(map(str, new_state))
        mask_val = eval(f"0b{mask}1111")

        return new_state, mask_val

    def switch(self, channels: List[int], mode: int) -> List[int]:
        try:
            self.validate(channels, mode)
        except ValueError as ve:
            logger.warning(ve)
        else:
            new_state, switch_val = self.calc_state(channels, mode)
            self.write_relay(switch_val)
            self.state_store.set(new_state)

        return self.state_store.get()

    def read(self):
        return self.state_store.get()


if __name__ == "__main__":
    RelayClient = RelayClient()

    # switch all one by one
    r = OFF_STATE
    for c in range(MIN_CHANNEL, MAX_CHANNEL + 1):
        RelayClient.switch([c], ON)
        time.sleep(1)

    # switch off one by one
    for c in range(MAX_CHANNEL, MIN_CHANNEL - 1, -1):
        RelayClient.switch([c], OFF)
        time.sleep(1)
