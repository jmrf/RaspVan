import argparse
import json
import logging
import os

from common.utils.io import init_logger
from common.utils.rabbit import BlockingQueueConsumer

logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


def on_event(event):
    print(f"Received an event: {event}")


def on_done():
    print("Completed! ")


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", "-q", help="Bind to a queue if provided")
    parser.add_argument(
        "--from_exchange",
        "-x",
        help="if provided the exchange to consume from",
    )
    parser.add_argument("--topic", "-t", help="topic as a routing key")

    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()

    try:
        exchange_name = args.from_exchange or ""
        exchange_type = "topic" if args.from_exchange else None
        routing_keys = [args.topic]

        if args.from_exchange and not args.topic:
            raise ValueError("A topic must be provided when consuming from an exchange")

        logger.info("Creating consumer and listening")
        consumer = BlockingQueueConsumer(
            "localhost",
            on_event,
            on_done,
            json.loads,
            routing_keys=routing_keys,
            exchange_name=exchange_name,
            exchange_type=exchange_type,
            queue_name=args.queue,
        )
        consumer.consume()
    except KeyboardInterrupt:
        logger.info("Closing connection and unbinding")
        # consumer.unbind()
        consumer.close()
