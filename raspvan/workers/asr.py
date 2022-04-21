import argparse
import asyncio
import os
import json
import logging

from asr.client import ASRClient
from asr.client import int_or_str

from common.utils.io import init_logger
from common.utils.exec import run_sync
from common.utils.rabbit import BlockingQueueConsumer

from raspvan.constants import AUDIO_DEVICE_ID_ENV_VAR
from raspvan.constants import Q_EXCHANGE_ENV_VAR

from respeaker.pixels import pixels


logger = logging.getLogger(__name__)
init_logger(level=logging.DEBUG, logger=logger)

AUDIO_DEVICE = int(os.getenv(AUDIO_DEVICE_ID_ENV_VAR, 0))


logger.info(f"🎤 Using Audio Device: {AUDIO_DEVICE}")


async def callback(event):
    logger.info("🚀 Received a request to launch ASR")
    text = "😕"
    try:
        # async with no_alsa_err:
        #     async with timeout(asr_max_time):
        res = await asr.stream_mic(sample_rate, device_id)
        text = res["text"]
    except Exception as e:
        logger.exception(f"Unknown error while runnig VAD/ASR callback: {e}")
    finally:
        pixels.off()

    logger.debug(f"🎤 Recognized: {text}")


def get_args():
    parser = argparse.ArgumentParser()

    comm_opts = parser.add_argument_group("Routing options")
    comm_opts.add_argument("--topic", "-t", help="topic as a routing key")

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
    global sample_rate
    global device_id
    global asr_max_time

    args = get_args()

    try:
        if not args.topic:
            raise ValueError(
                "A topic must be provided when consuming from an exchange "
                f"via '--topic' or setting '{Q_EXCHANGE_ENV_VAR}' env.variable."
            )

        # Init ASR parameters
        sample_rate = args.samplerate
        device_id = args.device
        asr_max_time = 10

        # Init the ASR Client
        asr = ASRClient(args.uri, args.vad_aggressiveness)

        # Init the triggering queue
        exchange_name = os.getenv(Q_EXCHANGE_ENV_VAR)
        exchange_type = "topic"
        routing_keys = [args.topic]

        consumer = BlockingQueueConsumer(
            "localhost",
            on_event=lambda e: run_sync(callback, e),
            on_done=lambda: pixels.off(),
            load_func=json.loads,
            routing_keys=routing_keys,
            exchange_name=exchange_name,
            exchange_type=exchange_type,
            queue_name="asr",
        )
        logger.info("🚀 Starting consuming from queue...")
        consumer.consume()
    except KeyboardInterrupt:
        logger.info("Closing connection and unbinding")
        consumer.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error while running ASR: {e}")
