from precise_runner import PreciseEngine, PreciseRunner

model_pb = "models/phiona/phiona.pb"
engine_binary = "/home/jose/code/Personal/RaspVan/hotword/precise/precise-engine"

engine = PreciseEngine(engine_binary, model_pb)
runner = PreciseRunner(engine, on_activation=lambda: print("hello"))
runner.start()

# Sleep forever
from time import sleep

while True:
    sleep(10)
