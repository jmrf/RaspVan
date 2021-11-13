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
from common.utils.decorators import deprecated
from common.utils.rabbit import BlockingQueueConsumer

from raspvan.constants import Q_EXCHANGE_ENV_VAR


logger = logging.getLogger(__name__)
init_logger(level=logging.DEBUG, logger=logger)


MODEL_PATH = "asr/models/deepspeech-0.9.3-models.pbmm"
SCORER_PATH = "asr/models/deepspeech-0.9.3-models.scorer"


logger.info(f"⚙️ Initializing model: {MODEL_PATH}")
model = deepspeech.Model(MODEL_PATH)

logger.info(f"⚙️ Initalizing scorer: {SCORER_PATH}")
model.enableExternalScorer(SCORER_PATH)

# Start audio with VAD
vad_audio = VADAudio(
    aggressiveness=3,
    device=None,
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
    logger.info("Listening (ctrl-C to exit)...")
    stream_context = model.createStream()

    frames = vad_audio.vad_collector()
    spinner = Halo(spinner="line")

    text = "😕"
    for frame in frames:
        if frame is not None:
            spinner.start()
            logging.debug("streaming frame")
            stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
        else:
            spinner.stop()
            logging.debug("end utterence")
            # Collect the text
            text = stream_context.finishStream()
            print(f"🎤 Recognized: {text}")
            stream_context = model.createStream()
            break

    return text


def callback(event):
    logger.info("Received a request to launch ASR")
    vad_listen()


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
