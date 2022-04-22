import argparse
import asyncio
import json
import logging
from typing import Dict
import wave
import webrtcvad
import websockets
import sounddevice as sd
from common import int_or_str

from common.utils.io import init_logger
from respeaker.pixels import Pixels


logger = logging.getLogger(__name__)
init_logger(level=logging.DEBUG, logger=logger)


class ASRClient:
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

    async def stream_mic(self, sample_rate: float, device_id) -> Dict[str, str]:
        def _callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            self.loop.call_soon_threadsafe(self.audio_queue.put_nowait, bytes(indata))

        # TODO: Make as parameters
        MAX_SECONDS_NO_VOICE = 5
        ASR_BLOCK_SIZE = 4000
        VAD_BLOCK_MS = 10
        VOICE_TH = 0.9

        asr_block_ms = ASR_BLOCK_SIZE / sample_rate * 1000  # 250ms
        vad_block_size = int(
            ASR_BLOCK_SIZE * VAD_BLOCK_MS // asr_block_ms
        )  # 160 frames
        buffer_size = int(asr_block_ms / VAD_BLOCK_MS)

        logger.debug(
            f"ASR Block ms: {asr_block_ms} "
            f"| VAD block size: {vad_block_size} "
            f"| Buffer size: {buffer_size}"
        )

        total_seconds_no_voice = 0
        buffer = []
        vads = []

        with sd.RawInputStream(
            samplerate=sample_rate,
            blocksize=vad_block_size,
            device=device_id,
            dtype="int16",
            channels=1,
            callback=_callback,
        ) as device:

            async with websockets.connect(self.asr_uri) as websocket:
                await websocket.send(
                    '{ "config" : { "sample_rate" : %d } }' % (device.samplerate)
                )

                self.pixels.speak()

                while True:
                    # Blocks of size 4000 @ 16kHz are 250 ms of audio
                    # we need 10,20 or 30 ms blocks for VAD so we collect smaller
                    # blocks and we only send to the ASR once we collected enough
                    data = await self.audio_queue.get()

                    if len(buffer) < buffer_size:
                        # PCM data buffer
                        buffer.append(data)
                        # VAD
                        _is_speech = self.vad.is_speech(data, int(device.samplerate))
                        vads.append(_is_speech)

                    else:
                        # Are 90% of the frames voice?
                        _is_voice = len(vads) and sum(vads) >= VOICE_TH * len(buffer)

                        # Send to ASR
                        if _is_voice:
                            self.pixels.think()
                            total_seconds_no_voice = 0

                            # ASR on the entire buffer
                            await websocket.send(b"".join(buffer))

                            res = json.loads(await websocket.recv())
                            logger.debug(res)

                            if "text" in res:
                                logger.info(
                                    f"💥 Voice detected. ASR result: {res['text']}"
                                )

                            self.pixels.speak()

                    total_seconds_no_voice += asr_block_ms / 1000
                    # Reset the buffers
                    buffer = []
                    vads = []

                    if total_seconds_no_voice >= MAX_SECONDS_NO_VOICE:
                        logger.debug("🚧 Breaking")
                        break

                self.pixels.off()

                await websocket.send('{"eof" : 1}')

                return json.loads(await websocket.recv())


async def main():
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
