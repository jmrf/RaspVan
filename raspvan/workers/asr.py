import argparse
import os
import json
import deepspeech
import logging
import numpy as np

from halo import Halo
from asr.audio import VADAudio
from asr.audio import DEFAULT_SAMPLE_RATE

from common.utils.io import init_logger
from common.utils.context import timeout
from common.utils.decorators import deprecated
from common.utils.rabbit import BlockingQueueConsumer

from raspvan.constants import AUDIO_DEVICE_ID_ENV_VAR
from raspvan.constants import ASR_MODEL_ENV_VAR
from raspvan.constants import ASR_SCORER_ENV_VAR
from raspvan.constants import Q_EXCHANGE_ENV_VAR


logger = logging.getLogger(__name__)
init_logger(level=logging.DEBUG, logger=logger)

AUDIO_DEVICE = int(os.getenv(AUDIO_DEVICE_ID_ENV_VAR, 0))
MODEL_PATH = os.getenv(ASR_MODEL_ENV_VAR)
SCORER_PATH = os.getenv(ASR_SCORER_ENV_VAR)

logger.info(f"🎤 Using Audio Device: {AUDIO_DEVICE}")

logger.info(f"⚙️ Initializing model: {MODEL_PATH}")
model = deepspeech.Model(MODEL_PATH)

logger.info(f"⚙️ Initalizing scorer: {SCORER_PATH}")
model.enableExternalScorer(SCORER_PATH)

# Start audio with VAD
vad_audio = VADAudio(
    aggressiveness=3,
    device=AUDIO_DEVICE,
    input_rate=DEFAULT_SAMPLE_RATE,
    file=None,
)


@deprecated
def old_pika_consume():
    import pika

    # Pika (rabbitMQ) client setup
    credentials = pika.PlainCredentials("guest", "guest")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq", credentials=credentials)
    )

    channel = connection.channel()
    channel.exchange_declare(exchange="asr-task", exchange_type="fanout")

    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange="asr-task", queue=queue_name)

    print("[*] Waiting for asr-task. To exit press CTRL+C")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()


def vad_listen():
    logger.info("Listening...")

    stream_context = model.createStream()
    frames = vad_audio.vad_collector()
    spinner = Halo(spinner="line")

    nones = 0
    rec = []

    for frame in frames:
        if frame is not None:
            spinner.start()
            stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
        else:

            text = stream_context.finishStream()

            rec.append(text)
            nones += 1
            print(f"end utterence. Nones: {nones}")

            if nones >= 2:
                break

            stream_context = model.createStream()

    spinner.stop()
    return rec


def callback(event, listen_time=10):
    logger.info("Received a request to launch ASR")
    text = "😕"
    try:
        with timeout(listen_time):
            text = vad_listen()
    except Exception as e:
        logger.warning(f"callback -> {e}")

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
