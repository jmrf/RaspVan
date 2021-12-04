import argparse
import os
import json
import logging

# import numpy as np

# from halo import Halo


from common.utils.io import init_logger
from common.utils.context import timeout
from common.utils.context import no_alsa_err
from common.utils.rabbit import BlockingQueueConsumer

from raspvan.constants import AUDIO_DEVICE_ID_ENV_VAR
from raspvan.constants import Q_EXCHANGE_ENV_VAR

from respeaker.pixels import pixels
from respeaker.record import record_audio


logger = logging.getLogger(__name__)
init_logger(level=logging.DEBUG, logger=logger)

AUDIO_DEVICE = int(os.getenv(AUDIO_DEVICE_ID_ENV_VAR, 0))


logger.info(f"🎤 Using Audio Device: {AUDIO_DEVICE}")


def callback(event, max_time=10):
    logger.info("Received a request to launch ASR")
    text = "😕"
    try:
        pixels.listen()
        with no_alsa_err:
            with timeout(max_time):
                # text = vad_listen()
                record_audio(record_seconds=4, output_filename="asr-recording.wav")
    except RuntimeError as re:
        logger.warning(f"VAD listening runtime error: {re}")
    except Exception as e:
        logger.exception(f"Unknown error while runnig callback -> {e}")
    finally:
        pixels.off()

    print(f"🎤 Recognized: {text}")


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", "-t", help="topic as a routing key")

    return parser.parse_args()


def run():

    args = get_args()

    try:
        if not args.topic:
            raise ValueError("A topic must be provided when consuming from an exchange")

        exchange_name = os.getenv(Q_EXCHANGE_ENV_VAR)
        exchange_type = "topic"
        routing_keys = [args.topic]

        consumer = BlockingQueueConsumer(
            "localhost",
            on_event=callback,
            on_done=lambda: print(f"Done! 🎤 "),
            load_func=json.loads,
            routing_keys=routing_keys,
            exchange_name=exchange_name,
            exchange_type=exchange_type,
        )
        logger.info("🚀 Starting consuming from queue...")
        consumer.consume()
    except KeyboardInterrupt:
        logger.info("Closing connection and unbinding")
        consumer.close()


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.error(f"Error while running ASR: {e}")
