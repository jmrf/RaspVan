import os
import json
import logging
import threading

from playsound import playsound
from time import sleep

from raspvan.constants import Q_EXCHANGE_ENV_VAR
from common.utils.io import init_logger
from common.utils.rabbit import BlockingQueuePublisher
from respeaker.pixels import pixels

from precise_runner import PreciseEngine
from precise_runner import PreciseRunner


logger = logging.getLogger(__name__)
init_logger(level=logging.INFO, logger=logger)

Q_TOPIC = "hotword"
COUNT = 0


class SoundThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.output = None

    def run(self):
        try:
            sound_path = (
                "/home/jose/code/Personal/RaspVan/assets/diagrams/hotword-ding-2.mp3"
            )
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
        amqp_uri="localhost",
        exchange_name=xchange,
        exchange_type="topic",
    )

    trigger = Trigger(publisher)

    # Init the Precise Engine & Runner
    logger.info("📢 Initializing hotword engine")
    engine = PreciseEngine(engine_binary, model_pb)
    runner = PreciseRunner(engine, on_activation=trigger.on_activation)

    logger.info("🚀 Ignition")
    runner.start()

    # Sleep forever
    while True:
        sleep(10)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.error(f"Error while running hotword detection: {e}")
