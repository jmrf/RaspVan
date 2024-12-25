import os
import random
import time

import click
import precise_runner
from halo import Halo
from precise_runner import PreciseEngine, PreciseRunner

from raspvan.constants import (
    HOTWORD_MODEL_DEFAULT_PATH,
    HOTWORD_MODEL_ENV_VAR,
    PRECISE_ENGINE_DEFAULT_BIN_PATH,
    PRECISE_ENGINE_ENV_VAR,
)
from respeaker.pixels import Pixels

print(f"Precise Runner version: {precise_runner.__version__}")

model_pb = os.getenv("HOTWORD_MODEL")
if model_pb is None:
    raise ValueError("'HOTWORD_MODEL' env. var not set.")

engine_binary = os.getenv("PRECISE_ENGINE")
if engine_binary is None:
    raise ValueError("'PRECISE_ENGINE' env. var not set.")



@click.command()
@click.option(
    "engine-binary",
    type=click.Path(dir_okay=False),
    default=os.getenv(PRECISE_ENGINE_ENV_VAR, PRECISE_ENGINE_DEFAULT_BIN_PATH)
)
@click.option(
    "model-pb",
    type=click.Path(dir_okay=False),
    default=os.getenv(HOTWORD_MODEL_ENV_VAR, HOTWORD_MODEL_DEFAULT_PATH)
)
def main(engine_binary, model_pb):
    pixels = Pixels(pattern_name="google")
    engine = PreciseEngine(engine_binary, model_pb)
    runner = PreciseRunner(
        engine,
        on_activation=lambda: pixels.wakeup() and print("👋🏼 Hello")
    )
    runner.start()

    with Halo(text="👂🏼 Listening...") as spinner:
        while True:
            print(random.choice(["😪", "😴", "💤"])
            time.sleep(10)


if __name__ == "_main__":
    main()

