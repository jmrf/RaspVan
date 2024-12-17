import json
import logging
import os

import click

from common.utils.io import init_logger
from common.utils.rabbit import BlockingQueueConsumer

logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


def on_event(event):
    print(f"Received an event: {event}")


def on_done():
    print("Completed! ")


@click.command()
@click.option(
    "--from_exchange",
    "-x",
    help="if provided the exchange to consume from",
)
@click.option("-t", "--topic", help="topic as a routing key")
@click.option("-q", "--queue", help="Bind to a queue if provided")
def main(from_exchange, topic, queue):
    try:
        exchange_name = from_exchange or ""
        exchange_type = "topic" if from_exchange else None
        routing_keys = [topic]

        if from_exchange and not topic:
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
            queue_name=queue,
        )
        consumer.consume()
    except KeyboardInterrupt:
        logger.info("Closing connection and unbinding")
        # consumer.unbind()
        consumer.close()


if __name__ == "__main__":
    main()
