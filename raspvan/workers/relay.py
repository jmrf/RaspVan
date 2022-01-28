import copy
import time

from smbus2 import SMBus

MIN_CHANNEL = 1
MAX_CHANNEL = 4
DEVICE_ADDR = 0x27

OFF_STATE = [1] * 4


def switch_relay(value: int):
    with SMBus(1) as bus:
        bus.write_byte_data(DEVICE_ADDR, 0, value)


def calc_state(channel, mode, state):
    new_state = copy.copy(state)
    new_state[channel - 1] = mode ^ 1
    mask = "".join(map(str, new_state))
    val = eval(f"0b{mask}1111")
    print(bin(val))

    return val, new_state


if __name__ == "__main__":
    # switch all one by one
    r = OFF_STATE
    for c in range(MIN_CHANNEL, MAX_CHANNEL + 1):
        switch_val, r = calc_state(c, 1, state=r)
        switch_relay(switch_val)
        time.sleep(1)

    # switch off one by one
    for c in range(MAX_CHANNEL, MIN_CHANNEL - 1, -1):
        switch_val, r = calc_state(c, 0, state=r)
        switch_relay(switch_val)
        time.sleep(1)
