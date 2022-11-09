import copy
import logging
import time
from typing import List

from smbus2 import SMBus

logger = logging.getLogger(__name__)

MIN_CHANNEL = 1
MAX_CHANNEL = 4
DEVICE_ADDR = 0x27

OFF_STATE = [1] * 4
ON = 1
OFF = 0


class Relayer:
    def __init__(self):
        self.state = OFF_STATE  # store this in Redis or similar!

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
        new_state = copy.copy(self.state)
        # new_state[channel - 1] = mode ^ 1

        if isinstance(channels, int):
            channels = [channels]

        for c in channels:
            new_state[c - 1] = mode ^ 1  # flip state

        mask = "".join(map(str, new_state))
        val = eval(f"0b{mask}1111")

        self.state = copy.copy(new_state)

        return val

    def switch(self, channels: List[int], mode: int):
        try:
            self.validate(channels, mode)
        except ValueError as ve:
            logger.warning(f"Error validating channels and mode: {ve}")
        else:
            switch_val = self.calc_state(channels, mode)
            self.write_relay(switch_val)


if __name__ == "__main__":
    relayer = Relayer()

    # switch all one by one
    r = OFF_STATE
    for c in range(MIN_CHANNEL, MAX_CHANNEL + 1):
        relayer.switch([c], ON)
        time.sleep(1)

    # switch off one by one
    for c in range(MAX_CHANNEL, MIN_CHANNEL - 1, -1):
        relayer.switch([c], OFF)
        time.sleep(1)
