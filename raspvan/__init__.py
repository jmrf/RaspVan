import logging
import os
import queue
from typing import Callable

import precise_runner
import requests
from precise_runner import PreciseEngine, PreciseRunner
from pyaudio import paInt16, PyAudio

from asr.client import ASRClient
from asr.vad import VAD
from common.utils.io import init_logger
from raspvan.constants import AUDIO_DEVICE_ID_ENV_VAR
from raspvan.workers.hotword import CHUNK_SIZE
from raspvan.workers.relay import RelayClient
from respeaker.pixels import Pixels

logger = logging.getLogger(__name__)
init_logger(
    level=os.getenv("LOGGING_LEVEL", logging.INFO),
    logger=logger,
)

# Simple communication Queue between components
HOTWORD_DETECTED = "HOTWORD_DETECTED"
ASR_READY = "ASR_READY"
NLU_READY = "NLU_READY"
q = queue.Queue()


def init_hotword_engine(
    engine_binary_path: str,
    hotword_model_pb: str,
    on_activation_func: Callable,
    custom_stream: bool = False,
    sample_rate: int = 16000,
    n_channels: int = 4,
):
    logger.debug(f"Precise Engine: '{engine_binary_path}'")
    logger.debug(f"Precise Runner version: '{precise_runner.__version__}'")
    logger.debug(f"Hotword Model path: '{hotword_model_pb}'")

    pa, stream = None, None
    if custom_stream:
        # Init the runner with a custom stream
        # so we can select the input device
        device_id = os.getenv(AUDIO_DEVICE_ID_ENV_VAR, 0)
        logger.info(f"🎙️ Initializing audio stream. Using device ID: {device_id}")

        pa = PyAudio()
        stream = pa.open(
            rate=sample_rate,
            channels=n_channels,
            format=paInt16,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            input_device_index=int(device_id),
        )

    # Init the Precise Engine
    logger.info("🔥 Initializing hotword engine")
    engine = PreciseEngine(engine_binary_path, hotword_model_pb, chunk_size=CHUNK_SIZE)

    # Init the precise runner (python wrapper over the engine)
    logger.info("🏃 Initializing hotword runner")
    runner = PreciseRunner(engine, on_activation=on_activation_func, stream=stream)

    return runner, pa, stream


async def pipeline(
    device,
    samplerate,
    vad_aggressiveness,
    hotword_engine,
    hotword_model,
    asr_uri,
    nlu_uri,
):
    logger.info(f"🎙️ Using Audio Device: {device} (sampling rate: {samplerate} Hz)")

    async def do_asr() -> None:
        try:
            # ASR: Start audio stream and do speach recognition on the fly
            logger.info("🔥 hotword detected! Starting microphone stream...")
            text = await asr.stream_mic(samplerate, device)
            res = {"key": ASR_READY, "text": text}
            logger.info(f"👂 {res}")
            q.put(res)
        except Exception as e:
            logger.error(f"Error making audio stream ASR: {e}")

    def do_nlu(text: str) -> None:
        try:
            # Request NLU parsing of the recognized text
            res = requests.post(nlu_uri, json={"text": text})
            res.raise_for_status()
            parsed = res.json()
            # Compose an Intent and Entities response object
            res = {
                "key": NLU_READY,
                "intent": parsed["intent"]["label"],
                "lights": [
                    e["value"]
                    for e in parsed["entities"]
                    if e["entity"] == "light_name"
                ],
            }
            logger.info(f"🔮 {res}")
            q.put(res)
        except Exception as e:
            logger.error(f"Error Performing NLU: {e}")

    def do_relay_switch() -> None:
        try:
            # Unpack all the recognized lights and map to channels
            channels = [
                channel for lname in msg["lights"] for channel in light_map.get(lname)
            ]
            # Switch On or Off: 1 or 0
            mode = int(msg["intent"] == "switch-on")
            rc.switch(channels, mode)
        except Exception as e:
            logger.error(f"Error switching relays: {e}")

    def activate():
        pixels.wakeup()
        q.put({"key": HOTWORD_DETECTED})

    # Init the Pixels client
    pixels = Pixels(pattern_name="google")

    # ---------------------------
    #     HOTWORD DETECTION
    # ---------------------------
    try:
        # Init the precise-engine machinery
        runner, _, _ = init_hotword_engine(
            engine_binary_path=hotword_engine,
            hotword_model_pb=hotword_model,
            on_activation_func=activate,
            sample_rate=samplerate,
        )
        # The runner runs on a separate thread...
        runner.start()
        logger.info("🚀 Hotword runner launched!")
    except Exception as e:
        raise Exception(f"Error in audio-stream or hotword engine: {e}")

    # ---------------------------
    #     ASR + NLU + Relays
    # ---------------------------
    logger.info("🤐 Initializing ASR and VAD clients")
    vad = VAD(vad_aggressiveness)
    asr = ASRClient(asr_uri, vad, pixels)
    rc = RelayClient()
    light_map = {
        "all": [0, 1, 2, 3],
        "main": [0],
        "rear": [1],
        "middle": [2],
        "front": [3],
    }

    # This requires to external services running (docker):
    #  - ASR websocket server
    #  - NLU http server
    logger.info(f"🔁 Starting ASR ({asr_uri}) + NLU ({nlu_uri}) infinite loop")
    while True:
        msg = q.get()
        key = msg["key"]
        if key == HOTWORD_DETECTED:
            await do_asr()
        elif key == ASR_READY:
            do_nlu(msg["text"])
        elif key == NLU_READY:
            do_relay_switch()
        else:
            logger.warning("😵‍💫 Weird message in the queue: '{msg}")

        pixels.off()
