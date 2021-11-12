import argparse
import os
import json

from src import logger
from src.constants import Q_EXCHANGE_ENV_VAR
from src.utils.decorators import deprecated
from src.utils.rabbit import BlockingQueueConsumer

import subprocess


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


def callback(event):
    logger.info("Received a request to launch ASR")
    # cmd = (
    #     "cat /root/audios/phiona-test-1.wav | "
    #     "/root/wav2letter/build/inference/inference/examples/simple_streaming_asr_example "
    #     "--input_files_base_path /root/model"
    # )
    cmd = (
        "/root/wav2letter/build/inference/inference/examples/multithreaded_streaming_asr_example "
        "--input_audio_files /root/audios/phiona-test-1.wav "
        "--input_files_base_path /root/model "
        "--output_files_base_path /root/audios"
    )
    ps = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        executable="/bin/bash",
    )
    output = ps.communicate()[0]
    print(output)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", "-t", help="topic as a routing key")

    return parser.parse_args()


def run():

    args = get_args()

    try:
        if args.from_exchange and not args.topic:
            raise ValueError("A topic must be provided when consuming from an exchange")

        exchange_name = os.getenv(Q_EXCHANGE_ENV_VAR)
        exchange_type = "topic"
        routing_keys = [args.topic]

        consumer = BlockingQueueConsumer(
            "localhost",
            on_event=callback,
            on_done=lambda x: print("Done!"),
            load_func=json.loads,
            routing_keys=routing_keys,
            exchange_name=exchange_name,
            exchange_type=exchange_type,
        )
        consumer.consume()
    except KeyboardInterrupt:
        logger.info("Closing connection and unbinding")
        consumer.close()


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.error(f"Error while running hotword detection: {e}")
