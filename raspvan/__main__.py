import asyncio
import os

import click

from common import int_or_str
from raspvan import pipeline
from raspvan.constants import (
    ASR_SERVER_DEFAULT_URI,
    ASR_SERVER_URI_ENV_VAR,
    AUDIO_DEFAULT_SAMPLE_RATE,
    AUDIO_DEVICE_ID_ENV_VAR,
    AUDIO_SAMPLE_RATE_ENV_VAR,
    HOTWORD_MODEL_DEFAULT_PATH,
    HOTWORD_MODEL_ENV_VAR,
    NLU_SERVER_DEFAULT_URI,
    NLU_SERVER_URI_ENV_VAR,
    PRECISE_ENGINE_DEFAULT_BIN_PATH,
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
@click.option(
    "-r",
    "--samplerate",
    type=int,
    help="sampling rate",
    default=os.getenv(AUDIO_SAMPLE_RATE_ENV_VAR, AUDIO_DEFAULT_SAMPLE_RATE),
)
# VAD options
@click.option(
    "-v", "--vad-aggressiveness", type=int, help="VAD aggressiveness", default=2
)
# Hotword detection options
@click.option(
    "-h",
    "--hotword-model",
    type=click.Path(dir_okay=False),
    default=os.getenv(HOTWORD_MODEL_ENV_VAR, HOTWORD_MODEL_DEFAULT_PATH),
)
@click.option(
    "-e",
    "--hotword-engine",
    type=click.Path(dir_okay=False),
    default=os.getenv(PRECISE_ENGINE_ENV_VAR, PRECISE_ENGINE_DEFAULT_BIN_PATH),
)
# ASR options
@click.option(
    "-as",
    "--asr-server-uri",
    help="ASR Server websocket URI",
    default=os.getenv(ASR_SERVER_URI_ENV_VAR, ASR_SERVER_DEFAULT_URI),
)
# NLU options
@click.option(
    "-ns",
    "--nlu-server-uri",
    help="NLU HTTP Server for Intent Classifier and Entity Tagger",
    default=os.getenv(NLU_SERVER_URI_ENV_VAR, NLU_SERVER_DEFAULT_URI),
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
