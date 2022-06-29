import argparse
import json
import logging
import os
import subprocess
import threading
import time
from datetime import datetime as dt
from time import sleep
from typing import Callable

import precise_runner
from precise_runner import PreciseEngine
from precise_runner import PreciseRunner
from pyaudio import paInt16
from pyaudio import PyAudio

from common import int_or_str
from common.utils.context import no_alsa_err
from common.utils.io import init_logger
from common.utils.rabbit import BlockingQueuePublisher
from common.utils.rabbit import get_amqp_uri_from_env
from raspvan.constants import AUDIO_DEVICE_ID_ENV_VAR
from raspvan.constants import DEFAULT_EXCHANGE
from raspvan.constants import DEFAULT_HOTWORD_ASR_TOPIC
from raspvan.constants import HOTWORD_MODEL_ENV_VAR
from raspvan.constants import PRECISE_ENGINE_ENV_VAR
from raspvan.constants import Q_EXCHANGE_ENV_VAR
from respeaker.pixels import Pixels

logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


CHUNK_SIZE = 2048
COUNT = 0


class SoundThread(threading.Thread):
    def __init__(self, timeout=3):
        threading.Thread.__init__(self)
        self.timeout = timeout

    def run(self):
        try:
            sound_path = os.path.join(os.getcwd(), "assets/hotword-ding.wav")
            logger.debug(f"Playing sound: {sound_path}")
            # playsound(sound_path)
            p = subprocess.Popen(["aplay", sound_path])
            try:
                p.wait(self.timeout)
            except subprocess.TimeoutExpired:
                p.kill()
        except Exception as e:
            logger.error(f"Error playing sound: {e}")


class ASRTrigger:
    def __init__(
        self, q_topic: str, pixels: Pixels, publisher: BlockingQueuePublisher
    ) -> None:
        self.publisher = publisher
        self.pixels = pixels

    def on_activation(self):
        global COUNT
        global publish_topic
        COUNT += 1

        logger.info(f" 🔫 Hotword detected! ({COUNT})")
        try:
            self.pixels.wakeup()
            SoundThread().start()
            # Send activation message through queue
            self.publisher.send_message(
                json.dumps([{"status": "detected", "timestamp": dt.now().isoformat()}]),
                topic=publish_topic,
            )
        except Exception as e:
            logger.error(f"Error sending Queue message: {e}")
        finally:
            # Switch off the wake up pixels
            time.sleep(0.5)
            self.pixels.off()


def init_engine(
    engine_binary_path: str,
    hotword_model_pb: str,
    on_activation_func: Callable,
    custom_stream: bool = False,
    sample_rate: int = 16000,
    n_channels: int = 4,
):

    logger.debug(f"Precise Engine: '{engine_binary_path}'")
    logger.debug(f"Precise Runner version: '{precise_runner.__version__}'")
    logger.debug(f"model path: '{hotword_model_pb}'")

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
    logger.info("⚙️ Initializing hotword engine")
    engine = PreciseEngine(engine_binary_path, hotword_model_pb, chunk_size=CHUNK_SIZE)

    # Init the precise runner (python wrapper over the engine)
    logger.info("⚙️ Initializing hotword runner")
    runner = PreciseRunner(engine, on_activation=on_activation_func, stream=stream)

    return runner, pa, stream


def get_args():
    parser = argparse.ArgumentParser()

    # rabbitMQ options
    comm_opts = parser.add_argument_group("Routing options")
    comm_opts.add_argument(
        "--exchange",
        "-x",
        help="queue exchange name",
        default=os.getenv(Q_EXCHANGE_ENV_VAR, DEFAULT_EXCHANGE),
    )
    comm_opts.add_argument(
        "--publish-topic",
        "-pt",
        help="HOTWORD --> ASR topic as a routing key",
        default=DEFAULT_HOTWORD_ASR_TOPIC,
    )
    # microphone options
    mic_opts = parser.add_argument_group("Audio options")
    mic_opts.add_argument(
        "-d",
        "--device",
        type=int_or_str,
        help="input device (numeric ID or substring)",
        default=os.getenv(AUDIO_DEVICE_ID_ENV_VAR, 0),
    )
    mic_opts.add_argument(
        "-r", "--samplerate", type=int, help="sampling rate", default=16000
    )
    # model options
    model_opts = parser.add_argument_group("Model and engine options")
    model_opts.add_argument("-m", "--model", default=os.getenv(HOTWORD_MODEL_ENV_VAR))
    model_opts.add_argument("-e", "--engine", default=os.getenv(PRECISE_ENGINE_ENV_VAR))

    args = parser.parse_args()

    if args.model is None:
        raise ValueError(
            f"--model not provided and '{HOTWORD_MODEL_ENV_VAR}' env. var not set."
        )

    if args.engine is None:
        raise ValueError(
            f"--engine not provided and '{PRECISE_ENGINE_ENV_VAR}' env. var not set."
        )

    return args


def main():

    args = get_args()

    try:
        global publish_topic

        publish_topic = args.publish_topic
        logger.info(
            f"🎙️ Using Audio Device: {args.device} "
            f"(sampling rate: {args.samplerate} Hz)"
        )

        # Init the rabbit MQ sender
        logger.info("🐇 Initializing publisher")
        amqp_host, amqp_port = get_amqp_uri_from_env()
        publisher = BlockingQueuePublisher(
            host=amqp_host,
            port=amqp_port,
            exchange_name=args.exchange,
            exchange_type="topic",
        )
    except Exception as e:
        raise Exception(f"Error initializing 🐇 publisher: {e}")

    try:
        trigger = ASRTrigger(args.publish_topic, Pixels(), publisher)
    except Exception as e:
        raise Exception(f"Error initializing ASR Trigger: {e}")

    try:
        # Init the precise-engine machinery
        runner, pa, stream = init_engine(
            engine_binary_path=args.engine,
            hotword_model_pb=args.model,
            on_activation_func=trigger.on_activation,
            sample_rate=args.samplerate,
        )
        # The runner runs on a separate thread...
        runner.start()
        logger.info("🚀 Runner launched!")
    except Exception as e:
        raise Exception(f"Error in audio-stream or hotword engine: {e}")
    else:
        # ...So here we just sleep for ever
        while True:
            sleep(10)

        if pa is not None:
            logger.warning("‼️ Terminating pyAudio!")
            pa.terminate()
            stream.stop_stream()


if __name__ == "__main__":
    try:
        with no_alsa_err():
            main()
    except Exception as e:
        logger.error(f"Error while running hotword detection: {e}")
        logger.exception("")
