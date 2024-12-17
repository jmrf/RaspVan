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
@click.option("-h", "--hotword_model", default=os.getenv(HOTWORD_MODEL_ENV_VAR))
@click.option("-e", "--hotword_engine", default=os.getenv(PRECISE_ENGINE_ENV_VAR))
# ASR options
@click.option(
    "-s",
    "--asr_server_uri",
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
    "-clf",
    "--classifier",
    help="Intent classifier model pkl file",
    default="nlu/models/intent-clf.pkl",
)
@click.option(
    "-le",
    "--label-encoder",
    help="Intent label encoder pkl file",
    default="nlu/models/intent-le.pkl",
)
@click.option(
    "-tg",
    "--tagger",
    help="Entity extractor pkl file",
    default="nlu/models/entity-tagger.pkl",
)
def main(
    device,
    samplerate,
    hotword_model,
    hotword_engine,
    asr_server_uri,
    vad_aggressiveness,
    classifier,
    label_encoder,
    tagger,
):
    asyncio.run(
        pipeline(
            hotword_engine=hotword_engine,
            hotword_model=hotword_model,
            asr_uri=asr_server_uri,
            nlu_classifier=classifier,
            nlu_label_encoder=label_encoder,
            nlu_tagger=tagger,
            samplerate=samplerate,
            device=device,
            vad_aggressiveness=vad_aggressiveness,
        )
    )


if __name__ == "__main__":
    main()
