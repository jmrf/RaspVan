import os
import json
import logging
import threading

from playsound import playsound
from pyaudio import PyAudio, paInt16
from time import sleep

from raspvan.constants import AUDIO_DEVICE_ID_ENV_VAR
from raspvan.constants import Q_EXCHANGE_ENV_VAR
from common.utils.io import init_logger
from common.utils.rabbit import BlockingQueuePublisher
from respeaker.pixels import pixels

from precise_runner import PreciseEngine
from precise_runner import PreciseRunner


logger = logging.getLogger(__name__)
init_logger(level=logging.DEBUG, logger=logger)

Q_TOPIC = "hotword"
CHUNK_SIZE = 2048
COUNT = 0


class SoundThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.output = None

    def run(self):
        try:
            sound_path = os.path.join(os.getcwd(), "assets/hotword-ding-2.mp3")
            playsound(sound_path)
        except Exception as e:
            logger.error(f"Error playing sound: {e}")


class Trigger:
    def __init__(self, publisher: BlockingQueuePublisher) -> None:
        self.publisher = publisher

    def on_activation(self):
        global COUNT
        COUNT += 1

        logger.info(f" 🔫 Hotword detected! ({COUNT})")
        pixels.wakeup()
        SoundThread().start()

        self.publisher.send_message(json.dumps(["active"]), topic=Q_TOPIC)

        pixels.off()


def run():
    model_pb = os.getenv("HOTWORD_MODEL")
    if model_pb is None:
        raise ValueError(f"'HOTWORD_MODEL' env. var not set.")

    engine_binary = os.getenv("PRECISE_ENGINE")
    if engine_binary is None:
        raise ValueError(f"'PRECISE_ENGINE' env. var not set.")

    xchange = os.getenv(Q_EXCHANGE_ENV_VAR)
    if xchange is None:
        raise ValueError(f"'{Q_EXCHANGE_ENV_VAR}' env. var not set.")

    # Init the rabbit MQ sender
    logger.info("🐇 Initializing publisher")
    publisher = BlockingQueuePublisher(
        amqp_uri="localhost",  # TODO: Make this configurable!
        exchange_name=xchange,
        exchange_type="topic",
    )

    # Init the Precise Engine
    logger.info("📢 Initializing hotword engine")
    engine = PreciseEngine(engine_binary, model_pb, chunk_size=CHUNK_SIZE)

    # Init the runner with a custom stream
    # so we can select the device
    device_id = os.getenv(AUDIO_DEVICE_ID_ENV_VAR, 0)
    logger.debug(f"Using device ID: {device_id}")
    pa = PyAudio()
    stream = pa.open(
        rate=16000,
        channels=4,
        format=paInt16,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
        input_device_index=int(device_id),
    )
    trigger = Trigger(publisher)
    runner = PreciseRunner(engine, on_activation=trigger.on_activation, stream=stream)

    logger.info("🚀 Ignition")
    runner.start()

    # trigger.on_activation()

    # Sleep forever
    while True:
        sleep(10)

    pa.terminate()
    stream.stop_stream()


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.error(f"Error while running hotword detection: {e}")
