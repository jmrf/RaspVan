import argparse
import asyncio
import json
import logging
import os
from datetime import datetime as dt

from asr.client import ASRClient
from asr.vad import VAD
from common import int_or_str
from common.utils.exec import run_sync
from common.utils.io import init_logger
from common.utils.rabbit import BlockingQueueConsumer
from common.utils.rabbit import get_amqp_uri_from_env
from raspvan.constants import AUDIO_DEVICE_ID_ENV_VAR
from raspvan.constants import DEFAULT_EXCHANGE
from raspvan.constants import DEFAULT_HOTWORD_ASR_TOPIC
from raspvan.constants import Q_EXCHANGE_ENV_VAR
from respeaker.pixels import Pixels


logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


last_time_asr_completed = dt.now().isoformat()


async def callback(event):
    global last_time_asr_completed
    text = "😕"
    try:
        if event["timestamp"] <= last_time_asr_completed:
            return

        logger.info(f"🚀 Launching ASR: {event}")
        text = await asr.stream_mic(sample_rate, device_id)
        logger.info(f"👂️ Recognized: {text}")
    except Exception as e:
        logger.exception(f"Unknown error while runnig VAD/ASR callback: {e}")
    finally:
        last_time_asr_completed = dt.now().isoformat()
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
        "--topic",
        "-t",
        help="topic as a routing key",
        default=DEFAULT_HOTWORD_ASR_TOPIC,
    )

    vad_opts = parser.add_argument_group("VAD options")
    vad_opts.add_argument(
        "-u",
        "--uri",
        type=str,
        metavar="URL",
        help="Server URL",
        default="ws://localhost:2700",
    )
    vad_opts.add_argument(
        "-d",
        "--device",
        type=int_or_str,
        help="input device (numeric ID or substring)",
        default=os.getenv(AUDIO_DEVICE_ID_ENV_VAR, 0),
    )
    vad_opts.add_argument(
        "-r", "--samplerate", type=int, help="sampling rate", default=16000
    )
    vad_opts.add_argument(
        "-v", "--vad-aggressiveness", type=int, help="VAD aggressiveness", default=2
    )

    return parser.parse_args()


async def main():

    global asr
    global device_id
    global sample_rate
    global pixels

    args = get_args()

    try:
        # Init ASR parameters
        sample_rate = args.samplerate
        device_id = args.device

        logger.info(
            f"🎙️ Using Audio Device: {args.device} "
            f"(sampling rate: {args.samplerate} Hz)"
        )

        # Init the Pixels client
        pixels = Pixels()

        # Init the ASR Client
        vad = VAD(args.vad_aggressiveness)
        asr = ASRClient(args.uri, vad)

        # Init the triggering queue
        amqp_host, amqp_port = get_amqp_uri_from_env()
        logger.debug(f"rabbit hot: {amqp_host}, rabbit port: {amqp_port}")
        logger.info(
            f"🐇 Connecting to exchange: {args.exchange} " f"(topics: {args.topic})"
        )

        consumer = BlockingQueueConsumer(
            host=amqp_host,
            port=amqp_port,
            on_event=lambda e: run_sync(callback, e),
            on_done=lambda: pixels.off(),
            load_func=json.loads,
            routing_keys=[args.topic],
            exchange_name=args.exchange,
            exchange_type="topic",
            queue_name="asr",
        )
        logger.info("👹 Starting consuming from queue...")
        consumer.consume()
    except KeyboardInterrupt:
        logger.info("Closing connection and unbinding")
        consumer.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error while running ASR: {e}")
