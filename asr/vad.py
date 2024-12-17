import logging
import os

import webrtcvad
from funcy import chunks

from asr import calc_block_size
from common.utils.io import init_logger

logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


class VAD:
    VALID_BLOCK_MS = [10, 20, 30]

    def __init__(self, vad_aggressiveness: int, voice_th: float = 0.9) -> None:
        self.voice_th = voice_th
        self.vad = webrtcvad.Vad(vad_aggressiveness)

    def is_voice(self, pcm_data, sample_rate: int, vad_block_ms: int = 30):
        if vad_block_ms not in self.VALID_BLOCK_MS:
            raise ValueError(f"vad_block_ms must be one of {self.VALID_BLOCK_MS}")

        # Chop the pcm buffer in chunks of max 30ms and do VAD
        vads = []
        vad_bytes = 2 * calc_block_size(vad_block_ms, sample_rate)  # int16 pcm data
        for pcm_chunk in chunks(vad_bytes, pcm_data):
            _is_speech = self.vad.is_speech(pcm_chunk, int(sample_rate))
            vads.append(_is_speech)

        # Are 90% of the frames voice?
        is_voice = len(vads) and sum(vads) >= self.voice_th * len(vads)
        return is_voice
