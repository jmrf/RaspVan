import asyncio
import os

import click

from common import int_or_str
from raspvan import pipeline
from raspvan.constants import (
    AUDIO_DEVICE_ID_ENV_VAR,
    HOTWORD_MODEL_ENV_VAR,
    PRECISE_ENGINE_ENV_VAR,
)


@click.command()
# Audio device options
@click.option(
    "-d",
    "--device",
    type=int_or_str,
    help="input device (numeric ID or substring)",
    default=os.getenv(AUDIO_DEVICE_ID_ENV_VAR, 0),
)
@click.option("-r", "--samplerate", type=int, help="sampling rate", default=16000)
# Hotword detection options
@click.option("-h", "--hotword-model", default=os.getenv(HOTWORD_MODEL_ENV_VAR))
@click.option("-e", "--hotword-engine", default=os.getenv(PRECISE_ENGINE_ENV_VAR))
# ASR options
@click.option(
    "-as",
    "--asr-server-uri",
    type=str,
    metavar="URL",
    help="ASR Server websocket URI",
    default="ws://localhost:2700",
)
# VAD options
@click.option(
    "-v", "--vad-aggressiveness", type=int, help="VAD aggressiveness", default=2
)
# NLU options
@click.option(
    "-ns",
    "--nlu-server-uri",
    help="NLU HTTP Server for Intent Classifier and Entity Tagger",
    default="http://localhost:8000",
)
def main(
    device,
    samplerate,
    vad_aggressiveness,
    hotword_engine,
    hotword_model,
    asr_server_uri,
    nlu_server_uri,
):
    asyncio.run(
        pipeline(
            device=int(device),
            samplerate=samplerate,
            vad_aggressiveness=vad_aggressiveness,
            hotword_engine=hotword_engine,
            hotword_model=hotword_model,
            asr_uri=asr_server_uri,
            nlu_uri=nlu_server_uri,
        )
    )


if __name__ == "__main__":
    main()
