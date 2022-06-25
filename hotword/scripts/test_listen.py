import os
import random
import time

import precise_runner
from precise_runner import PreciseEngine
from precise_runner import PreciseRunner


print(f"Precise Runner version: {precise_runner.__version__}")

model_pb = os.getenv("HOTWORD_MODEL")
if model_pb is None:
    raise ValueError(f"'HOTWORD_MODEL' env. var not set.")

engine_binary = os.getenv("PRECISE_ENGINE")
if engine_binary is None:
    raise ValueError(f"'PRECISE_ENGINE' env. var not set.")


engine = PreciseEngine(engine_binary, model_pb)

runner = PreciseRunner(engine, on_activation=lambda: print("hello"))
runner.start()

while True:
    face = random.choice(["😪", "😴", "💤"])
    print(f"{face} ...")
    time.sleep(2)
