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


@click.command()
@click.option(
    "engine-binary",
    type=click.Path(dir_okay=False),
    default=os.getenv(PRECISE_ENGINE_ENV_VAR, PRECISE_ENGINE_DEFAULT_BIN_PATH),
)
@click.option(
    "model-pb",
    type=click.Path(dir_okay=False),
    default=os.getenv(HOTWORD_MODEL_ENV_VAR, HOTWORD_MODEL_DEFAULT_PATH),
)
def main(engine_binary, model_pb):
    print(f"ℹ️ Precise Runner version: {precise_runner.__version__}")

    pixels = Pixels(pattern_name="google")
    engine = PreciseEngine(engine_binary, model_pb)
    runner = PreciseRunner(
        engine, on_activation=lambda: pixels.wakeup() and print("👋🏼 Hello")
    )
    runner.start()

    with Halo(text="👂🏼 Listening...") as spinner:
        while True:
            print(random.choice(["😪", "😴", "💤"]))
            time.sleep(10)

        spinner.success("✅ Done!")


if __name__ == "__main__":
    main()
