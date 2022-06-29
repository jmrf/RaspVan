import argparse
import json
import logging
import os
from datetime import datetime as dt

from common.utils.io import init_logger
from common.utils.rabbit import BlockingQueueConsumer
from common.utils.rabbit import BlockingQueuePublisher
from common.utils.rabbit import get_amqp_uri_from_env
from nlu import NLUPipeline
from raspvan.constants import DEFAULT_ASR_NLU_TOPIC
from raspvan.constants import DEFAULT_EXCHANGE
from raspvan.constants import DEFAULT_NLU_ACTION_TOPIC
from raspvan.constants import Q_EXCHANGE_ENV_VAR
from respeaker.pixels import Pixels


logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


def callback(event):
    global publish_topic
    global nlp

    text = "😕"
    try:
        text = event.get("text", "")
        if not text:
            return

        logger.info(f"🚀 Running NLU on: {text}")
        res = nlp([text])
        logger.info(f"🤔 Results: {res}")
        publisher.send_message(
            json.dumps(
                [
                    {
                        "results": res,
                        "status": "completed",
                        "timestamp": dt.now().isoformat(),
                    }
                ]
            ),
            topic=publish_topic,
        )
    except Exception as e:
        logger.exception(f"Unknown error while runnig NLU callback: {e}")
    finally:
        pixels.off()


def get_args():
    parser = argparse.ArgumentParser()

    comm_opts = parser.add_argument_group("Routing options")
    comm_opts.add_argument(
        "--exchange",
        "-x",
        help="queue exchange name",
        default=os.getenv(Q_EXCHANGE_ENV_VAR, DEFAULT_EXCHANGE),
    )
    comm_opts.add_argument(
        "--consume-topic",
        "-ct",
        help="topic as a routing key",
        default=DEFAULT_ASR_NLU_TOPIC,
    )
    comm_opts.add_argument(
        "--publish-topic",
        "-pt",
        help="ASR --> NLU topic as a routing key",
        default=DEFAULT_NLU_ACTION_TOPIC,
    )
    model_opts = parser.add_argument_group("Model options")
    model_opts.add_argument(
        "--classifier",
        "-clf",
        help="intent classifier model pkl file",
        default="nlu/models/intent-clf.pkl",
    )
    model_opts.add_argument(
        "--label-encoder",
        "-le",
        help="intent label encoder pkl file",
        default="nlu/models/intent-le.pkl",
    )
    model_opts.add_argument(
        "--tagger",
        "-tg",
        help="entity extractor pkl file",
        default="nlu/models/entity-tagger.pkl",
    )

    return parser.parse_args()


def main():

    global nlp
    global pixels
    global publisher
    global publish_topic

    args = get_args()

    try:
        # Init the Pixels client
        pixels = Pixels()

        # Init the NLU model pipeline
        nlp = NLUPipeline(args.classifier, args.label_encoder, args.tagger)

        # Init the triggering queue
        amqp_host, amqp_port = get_amqp_uri_from_env()

        # Init the rabbit MQ consumer
        logger.debug(f"rabbit host: {amqp_host}, rabbit port: {amqp_port}")
        logger.info(
            f"🐇 Initializing Consumer. Exchange: {args.exchange}"
            f"(topics: {args.consume_topic})"
        )
        consumer = BlockingQueueConsumer(
            host=amqp_host,
            port=amqp_port,
            on_event=lambda e: callback(e),
            on_done=lambda: pixels.off(),
            load_func=json.loads,
            routing_keys=[args.consume_topic],
            exchange_name=args.exchange,
            exchange_type="topic",
            queue_name="asr",
        )
        # Init the rabbit MQ sender
        publish_topic = args.publish_topic
        logger.info(
            f"🐇 Initializing publisher. Exchange: {args.exchange}"
            f"(topics: {publish_topic})"
        )
        publisher = BlockingQueuePublisher(
            host=amqp_host,
            port=amqp_port,
            exchange_name=args.exchange,
            exchange_type="topic",
            queue_name="nlu",
        )

        logger.info("👹 Starting consuming from queue...")
        consumer.consume()
    except KeyboardInterrupt:
        logger.info("Closing connection and unbinding")
        consumer.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error while running NLU: {e}")
