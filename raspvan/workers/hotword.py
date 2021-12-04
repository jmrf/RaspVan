import os
import json
import time
import logging
import threading

import subprocess

from pyaudio import PyAudio, paInt16
from time import sleep

from typing import Callable

from raspvan.constants import AUDIO_DEVICE_ID_ENV_VAR
from raspvan.constants import Q_EXCHANGE_ENV_VAR

from common.utils.context import no_alsa_err
from common.utils.io import init_logger
from common.utils.rabbit import BlockingQueuePublisher
from respeaker.pixels import pixels

import precise_runner
from precise_runner import PreciseEngine
from precise_runner import PreciseRunner

logger = logging.getLogger(__name__)
init_logger(level=logging.DEBUG, logger=logger)

Q_TOPIC = "hotword"
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


class Trigger:
    def __init__(self, publisher: BlockingQueuePublisher) -> None:
        self.publisher = publisher

    def on_activation(self):
        global COUNT
        COUNT += 1

        logger.info(f" 🔫 Hotword detected! ({COUNT})")
        try:
            pixels.wakeup()
            SoundThread().start()
            # Send activation message through queue
            self.publisher.send_message(json.dumps(["active"]), topic=Q_TOPIC)
            # Switch off the wake up pixels
        except Exception as e:
            logger.error(f"Error sending Queue message: {e}")
        finally:
            time.sleep(0.5)
            pixels.off()


def init_engine(on_activation_func: Callable, custom_stream: bool = False):
    # TODO: Make this env.var names constants
    model_pb = os.getenv("HOTWORD_MODEL")
    if model_pb is None:
        raise ValueError(f"'HOTWORD_MODEL' env. var not set.")

    engine_binary = os.getenv("PRECISE_ENGINE")
    if engine_binary is None:
        raise ValueError(f"'PRECISE_ENGINE' env. var not set.")

    logger.debug(f"Precise Engine: '{engine_binary}'")
    logger.debug(f"Precise Runner version: '{precise_runner.__version__}'")
    logger.debug(f"model path: '{model_pb}'")

    pa, stream = None, None
    if custom_stream:
        # Init the runner with a custom stream
        # so we can select the input device
        device_id = os.getenv(AUDIO_DEVICE_ID_ENV_VAR, 0)
        logger.info(f"📢 Initializing audio stream. Using device ID: {device_id}")

        pa = PyAudio()
        stream = pa.open(
            rate=16000,
            channels=4,
            format=paInt16,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
            input_device_index=int(device_id),
        )

    # Init the Precise Engine
    logger.info("⚙️ Initializing hotword engine")
    engine = PreciseEngine(engine_binary, model_pb, chunk_size=CHUNK_SIZE)

    # Init the precise runner (python wrapper over the engine)
    logger.info("⚙️ Initializing hotword runner")
    runner = PreciseRunner(engine, on_activation=on_activation_func, stream=stream)

    return runner, pa, stream


def run():
    xchange = os.getenv(Q_EXCHANGE_ENV_VAR)
    if xchange is None:
        raise ValueError(f"'{Q_EXCHANGE_ENV_VAR}' env. var not set.")

    try:
        # Init the rabbit MQ sender
        logger.info("🐇 Initializing publisher")
        publisher = BlockingQueuePublisher(
            amqp_uri="localhost",  # TODO: Make this configurable!
            exchange_name=xchange,
            exchange_type="topic",
        )
        trigger = Trigger(publisher)
    except Exception as e:
        raise Exception(f"Error initializing 🐇 publisher: {e}")

    try:
        # Init the precise machinery
        runner, pa, stream = init_engine(trigger.on_activation)
        runner.start()
        logger.info("🚀 Runner started!")
    except Exception as e:
        raise Exception(f"Error in audio-stream or hotword engine: {e}")
    else:
        # Sleep forever
        while True:
            sleep(10)

        if pa is not None:
            logger.warning("‼️ Terminating pyAudio!")
            pa.terminate()
            stream.stop_stream()


if __name__ == "__main__":
    try:
        with no_alsa_err():
            run()
    except Exception as e:
        logger.error(f"Error while running hotword detection: {e}")
        logger.exception("")
