import argparse
import asyncio
import json
import logging
import os
import time
import wave
from typing import Dict

import sounddevice as sd
import webrtcvad
import websockets
from funcy import chunks

from common import int_or_str
from common.utils.io import init_logger
from respeaker.pixels import Pixels


logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


class ASRClient:

    # TODO: Make as parameters
    MAX_SECONDS_NO_VOICE = 3
    ASR_BLOCK_SIZE = 4000
    VAD_BLOCK_MS = 30
    VOICE_TH = 0.9

    def __init__(self, asr_uri: str, vad_aggressiveness: int = 2) -> None:
        self.asr_uri = asr_uri
        self.loop = asyncio.get_running_loop()
        self.audio_queue = asyncio.Queue()
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.pixels = Pixels()

    async def from_wave(self, wave_file: str) -> Dict[str, str]:
        async with websockets.connect(self.asr_uri) as websocket:

            wf = wave.open(wave_file, "rb")
            await websocket.send(
                '{ "config" : { "sample_rate" : %d } }' % (wf.getframerate())
            )
            buffer_size = int(wf.getframerate() * 0.2)  # 0.2 seconds of audio
            while True:
                data = wf.readframes(buffer_size)
                if len(data) == 0:
                    break

                await websocket.send(data)
                logger.debug(await websocket.recv())

            await websocket.send('{"eof" : 1}')

            return json.loads(await websocket.recv())

    def _is_voice(self, pcm_data, sample_rate, vad_block_size):
        vads = []
        # VAD: chop the pcm buffer is chunks of max 30ms and do VAD
        vad_bytes = 2 * vad_block_size
        for pcm_chunk in chunks(vad_bytes, pcm_data):
            _is_speech = self.vad.is_speech(pcm_chunk, int(sample_rate))
            vads.append(_is_speech)
            # logger.debug(
            #     f"VADing a pcm of {len(pcm_chunk)} bytes "
            #     f"(total: {len(pcm_data)}) -> speech: {_is_speech}"
            # )

        # Are 90% of the frames voice?
        is_voice = len(vads) and sum(vads) >= self.VOICE_TH * len(vads)
        return is_voice

    async def stream_mic(self, sample_rate: float, device_id: int) -> Dict[str, str]:
        def _callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            self.loop.call_soon_threadsafe(self.audio_queue.put_nowait, bytes(indata))

        async def _do_asr(pcm_data):
            # ASR on the entire buffer
            await websocket.send(pcm_data)

            res = json.loads(await websocket.recv())
            logger.debug(res)

            if "text" in res:
                logger.info(f"ASR result: {res['text']}")

        # Compute pcm buffer parameters
        asr_block_ms = self.ASR_BLOCK_SIZE / sample_rate * 1000  # e.g: 250ms
        vad_block_size = int(self.ASR_BLOCK_SIZE * self.VAD_BLOCK_MS // asr_block_ms)

        logger.debug(
            f"ASR Block ms: {asr_block_ms} | VAD block size: {vad_block_size} "
        )

        with sd.RawInputStream(
            samplerate=sample_rate,
            blocksize=self.ASR_BLOCK_SIZE,
            device=device_id,
            dtype="int16",
            channels=1,
            callback=_callback,
        ) as device:
            # Blocks of size 4000 @ 16kHz are 250 ms of audio
            # however for VAD we need 10,20 or 30 ms blocks
            async with websockets.connect(self.asr_uri) as websocket:
                await websocket.send(
                    '{ "config" : { "sample_rate" : %d } }' % (device.samplerate)
                )

                self.pixels.speak()
                start = time.time()
                # t_last_voice = start
                total_seconds_no_voice = 0
                i = 0
                while True:
                    i += 1
                    data = await self.audio_queue.get()

                    if self._is_voice(data, device.samplerate, vad_block_size):
                        # self.pixels.think()
                        # NOTE: While we run the ASR the microphone continues
                        # to collect audio frames and potentially we can
                        # break to having 'silent' audio blocks before
                        # the ASR has compelted!
                        logger.debug(f"🎙️ Running ASR! (block {i})")
                        total_seconds_no_voice = 0
                        await _do_asr(data)
                        # t_last_voice = time.time()
                        # self.pixels.speak()
                    else:
                        # time from microphone perspective
                        total_seconds_no_voice += asr_block_ms / 1000

                    # Alternatively: time from last ASR result:
                    # total_seconds_no_voice = time.time() - t_last_voice

                    if total_seconds_no_voice >= self.MAX_SECONDS_NO_VOICE:
                        logger.debug(
                            f"🛑 Stopped listening after {total_seconds_no_voice}s "
                            f"without detecting voice (block {i})"
                        )
                        break

                logger.debug(f"⏳️ Total run time: {time.time() - start}")
                self.pixels.off()

                await websocket.send('{"eof" : 1}')

                return json.loads(await websocket.recv())


async def main():
    """Here just to serve as an example of how to run as standalone"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--uri",
        type=str,
        metavar="URL",
        help="Server URL",
        default="ws://localhost:2700",
    )
    parser.add_argument("-f", "--file", type=str, help="wave file to ASR", default=None)
    parser.add_argument(
        "-d",
        "--device",
        type=int_or_str,
        help="input device (numeric ID or substring)",
        default=0,
    )
    parser.add_argument(
        "-r", "--samplerate", type=int, help="sampling rate", default=16000
    )
    parser.add_argument(
        "-v", "--vad-aggressiveness", type=int, help="VAD aggressiveness", default=1
    )

    args = parser.parse_args()

    asr = ASRClient(args.uri, args.vad_aggressiveness)
    if args.file:
        res = await asr.from_wave(args.file)
    else:
        res = await asr.stream_mic(args.samplerate, args.device)

    logger.info(f"📢: {res}")


if __name__ == "__main__":
    # python -m  asr.client -v 2 -d 0
    asyncio.run(main())
