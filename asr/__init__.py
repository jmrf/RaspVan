import numpy as np


def raw_stream_to_numpy(buffer, dtype: str, channels: int):
    data = np.frombuffer(buffer, dtype=dtype)
    data = data.reshape(-1, channels)

    return data


def calc_block_size(block_ms: int, sample_rate: int) -> int:
    return int(block_ms * sample_rate / 1000)


def calc_block_ms(block_size: int, sample_rate: int) -> int:
    return int(block_size / sample_rate * 1000)
