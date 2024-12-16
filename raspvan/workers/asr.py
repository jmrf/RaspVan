import asyncio
import json
import logging
import os
from datetime import datetime as dt

import click

from asr.client import ASRClient
from asr.vad import VAD
from common import int_or_str
from common.utils.exec import run_sync
from common.utils.io import init_logger
from common.utils.rabbit import (BlockingQueueConsumer, BlockingQueuePublisher,
                                 get_amqp_uri_from_env)
from raspvan.constants import (AUDIO_DEVICE_ID_ENV_VAR, DEFAULT_ASR_NLU_TOPIC,
                               DEFAULT_EXCHANGE, DEFAULT_HOTWORD_ASR_TOPIC,
                               Q_EXCHANGE_ENV_VAR)
from respeaker.pixels import Pixels

logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


last_time_asr_completed = dt.now().isoformat()


async def callback(event):
    global last_time_asr_completed
    global publish_topic

    text = "😕"
    try:
        if event["timestamp"] <= last_time_asr_completed:
            return

        logger.info(f"🚀 Launching ASR: {event}")
        text = await asr.stream_mic(sample_rate, device_id)
        logger.info(f"👂️ Recognized: {text}")
        publisher.send_message(
            json.dumps(
                [
                    {
                        "text": text,
                        "status": "completed",
                        "timestamp": dt.now().isoformat(),
                    }
                ]
            ),
            topic=publish_topic,
        )
    except Exception as e:
        logger.exception(f"Unknown error while runnig VAD/ASR callback: {e}")
    finally:
        last_time_asr_completed = dt.now().isoformat()
        pixels.off()


async def arun_asr(
    samplerate, device, uri, exchange, consume_topic, publish_topic, vad_aggressiveness
):
    global asr
    global device_id
    global sample_rate
    global pixels
    global publisher

    try:
        # Init ASR parameters
        sample_rate = samplerate
        device_id = device

        logger.info(
            f"🎙️ Using Audio Device: {device} " f"(sampling rate: {samplerate} Hz)"
        )

        # Init the Pixels client
        pixels = Pixels()

        # Init the ASR Client
        vad = VAD(vad_aggressiveness)
        asr = ASRClient(uri, vad)

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
            on_event=lambda e: run_sync(callback, e),
            on_done=lambda: pixels.off(),
            load_func=json.loads,
            routing_keys=[consume_topic],
            exchange_name=exchange,
            exchange_type="topic",
            queue_name="asr",
        )
        # Init the rabbit MQ sender
        logger.info(
            f"🐇 Initializing publisher. Exchange: {exchange}"
            f"(topics: {publish_topic})"
        )
        publish_topic = publish_topic
        publisher = BlockingQueuePublisher(
            host=amqp_host,
            port=amqp_port,
            exchange_name=exchange,
            exchange_type="topic",
            queue_name="nlu",
        )
        logger.info("👹 Starting consuming from queue...")
        consumer.consume()
    except KeyboardInterrupt:
        logger.info("Closing connection and unbinding")
        consumer.close()


@click.command()
@click.option(
    "-x",
    "--exchange",
    help="queue exchange name",
    default=os.getenv(Q_EXCHANGE_ENV_VAR, DEFAULT_EXCHANGE),
)
@click.option(
    "-ct",
    "--consume-topic",
    help="ASR --> NLU topic as a routing key",
    default=DEFAULT_HOTWORD_ASR_TOPIC,
)
@click.option(
    "-pt",
    "--publish-topic",
    help="ASR --> NLU topic as a routing key",
    default=DEFAULT_ASR_NLU_TOPIC,
)
@click.option(
    "-s",
    "--asr-ws-uri",
    type=str,
    metavar="URL",
    help="ASR Server websocket URI",
    default="ws://localhost:2700",
)
@click.option(
    "-d",
    "--device",
    type=int_or_str,
    help="input device (numeric ID or substring)",
    default=os.getenv(AUDIO_DEVICE_ID_ENV_VAR, 0),
)
@click.option("-r", "--samplerate", type=int, help="sampling rate", default=16000)
@click.option(
    "-v", "--vad-aggressiveness", type=int, help="VAD aggressiveness", default=2
)
def main(
    samplerate,
    device,
    asr_ws_uri,
    exchange,
    consume_topic,
    publish_topic,
    vad_aggressiveness,
):
    try:
        asyncio.run(
            arun_asr(
                samplerate,
                device,
                asr_ws_uri,
                exchange,
                consume_topic,
                publish_topic,
                vad_aggressiveness,
            )
        )
    except Exception as e:
        logger.exception(f"💥 Error while running ASR: {e}")


if __name__ == "__main__":
    main()
