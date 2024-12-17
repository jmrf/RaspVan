import logging
import os
import queue
from typing import Callable

import precise_runner
from precise_runner import PreciseEngine, PreciseRunner
from pyaudio import paInt16, PyAudio

from asr.client import ASRClient
from asr.vad import VAD
from common.utils.io import init_logger
from nlu import NLUPipeline
from raspvan.constants import AUDIO_DEVICE_ID_ENV_VAR
from raspvan.workers.hotword import CHUNK_SIZE
from respeaker.pixels import Pixels

logger = logging.getLogger(__name__)
init_logger(
    level=os.getenv("LOGGING_LEVEL", logging.INFO),
    logger=logger,
)

# Simple communication Queue between components
HOTWORD_KEY = "HOTWORD"
ASR_KEY = "ASR"
NLU_KEY = "NLU"
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
    hotword_engine,
    hotword_model,
    asr_uri,
    nlu_classifier,
    nlu_label_encoder,
    nlu_tagger,
    samplerate,
    device,
    vad_aggressiveness,
):
    logger.info(f"🎙️ Using Audio Device: {device} " f"(sampling rate: {samplerate} Hz)")
    # Init the Pixels client
    pixels = Pixels(pattern_name="google")

    # Init the ASR Client
    # ---------------------------
    #     HOTWORD DETECTION
    # ---------------------------
    def activate():
        pixels.wakeup()
        q.put(HOTWORD_KEY)

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
    #           ASR + NLU
    # ---------------------------
    logger.info("🤐 Initializing ASR and VAD clients")
    vad = VAD(vad_aggressiveness)
    asr = ASRClient(asr_uri, vad, pixels)

    # FIXME: This fucker needs a different numpy! :(
    logger.info("🔮 Initializing NLU pipeline")
    nlp = NLUPipeline(nlu_classifier, nlu_label_encoder, nlu_tagger)

    logger.info(f"🔁 Starting ASR ({asr_uri}) + NLU infinite loop")
    while True:
        msg = q.get()
        if msg == HOTWORD_KEY:
            # Start audio stream and ASR on the fly
            logger.info("🔥 hotword detected! Starting microphone stream...")
            text = await asr.stream_mic(samplerate, device)
            logger.info("👂 Recognized: '{text}")
            q.put(f"{ASR_KEY}:{text}")
        elif msg.startswith(ASR_KEY):
            # NLU analysis of the recognized text
            text = msg.split(":")[-1]
            logger.info(f"🤔 Parsing '{text}'")
            res = nlp([text])
            print(res)
        else:
            logger.warning("😵‍💫 Weird message in the queue: '{msg}")

        pixels.off()
