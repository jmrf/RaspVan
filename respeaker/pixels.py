import logging
import os
import random
import threading
import time

from gpiozero import LED

from common.utils.io import init_logger

try:
    import queue as Queue
except ImportError:
    import Queue as Queue


from common import Singleton
from respeaker.led import apa102
from respeaker.led.alexa_led_pattern import AlexaLedPattern
from respeaker.led.google_home_led_pattern import GoogleHomeLedPattern

logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


class Pixels(metaclass=Singleton):
    PIXELS_N = 12
    PATTERN_MAP = {"google": GoogleHomeLedPattern, "alexa": AlexaLedPattern}

    def __init__(self, pattern=None):
        if pattern is None:
            pattern = self._random_pattern()

        self.pattern = pattern(show=self.show)

        self.dev = apa102.APA102(num_led=self.PIXELS_N)

        self.power = LED(5)
        self.power.on()

        self.queue = Queue.Queue()
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

        self.last_direction = None

    def _run(self):
        while True:
            func = self.queue.get()
            # logger.debug(f"💡 elements in the queue: {self.queue.qsize()}")
            # logger.debug(f"💡 func: {func.__name__}")
            self.pattern.stop = False
            func()

    def _random_pattern(self):
        return self.PATTERN_MAP[
            os.getenv("PIXELS_PATTERN", random.choice(list(self.PATTERN_MAP.keys())))
        ]

    def wakeup(self, direction=0):
        self.last_direction = direction

        def f():
            self.pattern.wakeup(direction)

        self.put(f)

    def listen(self):
        if self.last_direction:

            def f():
                self.pattern.wakeup(self.last_direction)

            self.put(f)
        else:
            self.put(self.pattern.listen)

    def think(self):
        self.put(self.pattern.think)

    def speak(self):
        self.put(self.pattern.speak)

    def off(self):
        self.put(self.pattern.off)

    def put(self, func):
        self.pattern.stop = True
        self.queue.put(func)

    def show(self, data):
        for i in range(self.PIXELS_N):
            self.dev.set_pixel(
                i, int(data[4 * i + 1]), int(data[4 * i + 2]), int(data[4 * i + 3])
            )

        self.dev.show()


if __name__ == "__main__":
    pixels = Pixels()

    while True:
        try:
            print("🌞 wakeup...")
            pixels.wakeup()
            time.sleep(3)
            print("🤔 think...")
            pixels.think()
            time.sleep(3)
            print("🗣️  speak...")
            pixels.speak()
            time.sleep(6)
            print("👋 off...")
            pixels.off()
            time.sleep(3)
        except KeyboardInterrupt:
            break
        finally:
            pixels.off()
            time.sleep(1)
