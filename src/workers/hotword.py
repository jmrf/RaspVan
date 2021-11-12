import os
import json

from time import sleep

from src import logger
from src.utils.rabbit import BlockingQueuePublisher

from precise_runner import PreciseEngine
from precise_runner import PreciseRunner


Q_TOPIC = "hotword"
Q_NAME = "hotword"
X_CHANGE = "fiona"


def run():
    model_pb = os.getenv("HOTWORD_MODEL_PB")
    if model_pb is None:
        raise ValueError(f"'HOTWORD_MODEL_PB' env. var not set.")

    engine_binary = os.getenv("PRECISE_ENGINE")
    if engine_binary is None:
        raise ValueError(f"'PRECISE_ENGINE' env. var not set.")

    # Init the rabbit MQ sender
    logger.info("🐇 Initializing publisher")
    publisher = BlockingQueuePublisher(
        amqp_uri="localhost",
        queue_name=Q_NAME,
        exchange_name=X_CHANGE,
        exchange_type="topic",
    )

    # Init the Precise Engine & Runner
    logger.info("📢 Initializing hotword engine")
    engine = PreciseEngine(engine_binary, model_pb)
    runner = PreciseRunner(
        engine,
        on_activation=lambda: publisher.send_message(
            json.dumps(["active"]), topic=Q_TOPIC
        ),
    )

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
