import json
import logging
import os
from datetime import datetime as dt

import click

from common.utils.io import init_logger
from common.utils.rabbit import (
    BlockingQueueConsumer,
    BlockingQueuePublisher,
    get_amqp_uri_from_env,
)
from nlu import NLUPipeline
from raspvan.constants import (
    DEFAULT_ASR_NLU_TOPIC,
    DEFAULT_EXCHANGE,
    DEFAULT_NLU_ACTION_TOPIC,
    Q_EXCHANGE_ENV_VAR,
)
from respeaker.pixels import Pixels

logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


NLP = None
PUBLISH_TOPIC = None


def callback(event):
    text = "😕"
    try:
        text = event.get("text", "")
        if not text:
            return

        logger.info(f"🚀 Running NLU on: '{text}'")
        res = NLP([text])
        logger.info(f"🤔 Results: {res}")
        PUBLISHER.send_message(
            json.dumps(
                [
                    {
                        "results": res,
                        "status": "completed",
                        "timestamp": dt.now().isoformat(),
                    }
                ]
            ),
            topic=PUBLISH_TOPIC,
        )
    except Exception as e:
        logger.exception(f"Unknown error while runnig NLU callback: {e}")
    finally:
        PIXELS.off()


@click.command()
@click.option_group(
    "Routing options",
    help="MQTT Routing Options",
    options=["--exchange", "--consume-topic", "--publish-topic"],
)
@click.option(
    "-x",
    "--exchange",
    help="queue exchange name",
    default=os.getenv(Q_EXCHANGE_ENV_VAR, DEFAULT_EXCHANGE),
)
@click.option(
    "-ct",
    "--consume-topic",
    help="topic as a routing key",
    default=DEFAULT_ASR_NLU_TOPIC,
)
@click.option(
    "-pt",
    "--publish-topic",
    help="ASR --> NLU topic as a routing key",
    default=DEFAULT_NLU_ACTION_TOPIC,
)
@click.option_group("Model options", options=["--clf", "--le", "--tg"])
@click.option(
    "-clf",
    "--classifier",
    help="intent classifier model pkl file",
    default="nlu/models/intent-clf.pkl",
)
@click.option(
    "-le",
    "--label-encoder",
    help="intent label encoder pkl file",
    default="nlu/models/intent-le.pkl",
)
@click.option(
    "-tg",
    "--tagger",
    help="entity extractor pkl file",
    default="nlu/models/entity-tagger.pkl",
)
def main(classifier, label_encoder, tagger, exchange, consume_topic, publish_topic):
    global PUBLISH_TOPIC
    global PUBLISHER
    global PIXELS
    global NLP
    try:
        # Init the Pixels client
        PIXELS = Pixels()

        # Init the NLU model pipeline
        NLP = NLUPipeline(classifier, label_encoder, tagger)

        # Init the triggering queue
        amqp_host, amqp_port = get_amqp_uri_from_env()

        # Init the rabbit MQ consumer
        logger.debug(f"rabbit host: {amqp_host}, rabbit port: {amqp_port}")
        logger.info(
            f"🐇 Initializing Consumer. Exchange: {exchange}"
            f"(topics: {consume_topic})"
        )
        consumer = BlockingQueueConsumer(
            host=amqp_host,
            port=amqp_port,
            on_event=lambda e: callback(e),
            on_done=lambda: PIXELS.off(),
            load_func=json.loads,
            routing_keys=[consume_topic],
            exchange_name=exchange,
            exchange_type="topic",
            queue_name="asr",
        )
        # Init the rabbit MQ sender
        PUBLISH_TOPIC = publish_topic
        logger.info(
            f"🐇 Initializing publisher. Exchange: {exchange}"
            f"(topics: {publish_topic})"
        )
        PUBLISHER = BlockingQueuePublisher(
            host=amqp_host,
            port=amqp_port,
            exchange_name=exchange,
            exchange_type="topic",
            queue_name="nlu",
        )
        # Listen from Queue for new message to run NLP on
        logger.info("👹 Starting consuming from queue...")
        consumer.consume()
    except KeyboardInterrupt:
        logger.info("Closing connection and unbinding")
        consumer.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Error while running NLU: {e}")
