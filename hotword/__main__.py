import os
import random
import time

import click
import precise_runner
from halo import Halo
from precise_runner import PreciseEngine, PreciseRunner


@click.command()
@click.option(
    "-e",
    "--engine-binary",
    type=click.Path(dir_okay=False),
    default=os.getenv("HOTWORD_MODEL_PB_PATH"),
)
@click.option(
    "-m",
    "--model-pb",
    type=click.Path(dir_okay=False),
    default=os.getenv("PRECISE_ENGINE_BIN_PATH"),
)
def main(engine_binary, model_pb):
    print(f"ℹ️ Precise Runner version: {precise_runner.__version__}")

    if engine_binary is None or not os.path.exists(engine_binary):
        print("A valid 'engine_binary' path must be provided")
        exit(1)
    if model_pb is None or not os.path.exists(model_pb):
        print("A valid 'model_pb' path must be provided")
        exit(1)

    print(f"⚙️ Precise Engine: {engine_binary}")
    print(f"🔮 Hotword model : {model_pb}")

    # pixels = Pixels(pattern_name="google")
    engine = PreciseEngine(engine_binary, model_pb)
    runner = PreciseRunner(engine, on_activation=lambda: print("👋🏼 Hello"))
    runner.start()

    with Halo(text="👂🏼 Listening...") as spinner:
        while True:
            print(random.choice(["😪", "😴", "💤"]))
            time.sleep(10)

        spinner.success("✅ Done!")


if __name__ == "__main__":
    main()
