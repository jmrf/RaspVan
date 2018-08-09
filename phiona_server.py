import json
import logging
import argparse
import time

import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from tendo import colorer

from flask import Flask, request
from flask_restful import Resource, Api

# RapberryPi GPIO control
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
PORT_MAPPING = {
    "main": 7,
    "l1": 11,
    "l2": 13,
    "l3": 15
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# logger file handler
fh = logging.FileHandler('phiona_server.log')
fh.setLevel(logging.DEBUG)

# logger console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# logger formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


# Flask app
app = Flask("RaspberryPiServer")
api = Api(app)


def read_pin_states():
    return dict([
        ("{}".format(k, pin_n), 'OFF' if GPIO.input(pin_n) else 'ON')
        for k, pin_n in PORT_MAPPING.items()
    ])


def switch_light(light_name, signal):
    if light_name in PORT_MAPPING:
        logger.info("Switching light '{}' --> {}".format(light_name, 'ON' if signal else 'OFF'))
        GPIO.output(
            PORT_MAPPING[light_name],
            GPIO.HIGH if not signal else GPIO.LOW   # low side switch => (ON => 0v | OFF => 3.3v)
        )
        return {light_name: 'OFF' if GPIO.input(PORT_MAPPING[light_name]) else 'ON'}
    else:
        msg = "Light '{}' not recognized. Ignoring request...".format(light_name)
        logger.warning(msg)
        return {"error": msg}


class LightTimer(Resource):

    def __init__(self):
        self.sched = BackgroundScheduler(daemon=True)

    def scheduled_switch(self, light_name, signal, id):
        switch_light(light_name, signal)
        self.sched.remove_job(id)

    def get(self):
        pass

    def post(self):
        try:
            json_data = request.get_json(force=True)

            for k, v in json_data.items():
                l_name, signal, delay = k, v['signal'], v['delay']
                logger.info("{} ==> {} in {} seconds".format(l_name, "ON" if signal else "OFF", delay))
                job_id = "{}-{}-{}".format(l_name, signal, delay)
                self.sched.add_job(
                    self.scheduled_switch,
                    'interval',
                    seconds=delay,
                    id=job_id,
                    args=(l_name, signal, job_id,)
                )
                self.sched.start()
            return {"timers": [k for k in json_data.keys()]}

        except Exception as e:
            logger.error("Error in POST request: {}".format(e))
            logger.exception(e)


class RaspberryPiServer(Resource):

    def __init__(self):
        logger.info("Initiating Phiona Server...")

    def get(self):
        # read the state of the pins and return
        return read_pin_states()

    def post(self):
        try:
            json_data = request.get_json(force=True)
            for k, v in json_data.items():
                return switch_light(k, v)


        except Exception as e:
            logger.error("Error in POST request: {}".format(e))
            logger.exception(e)


def set_IO_pins():
    """
    We will be using the following physical ports:
     * pin n6  (GND)     =>  (no configuration required)
     * pin n7  (GPIO 4)  => light n1
     * pin n11 (GPIO 17) => light n2
     * pin n13 (GPIO 27) => light n3
     * pin n15 (GPIO 22) => light n4
    """
    logger.info("Setting PIN numbering to physical")
    for p in PORT_MAPPING.values():
        try:
            GPIO.setup(p, GPIO.OUT)
            logger.info("Setting physical pin={} in OUTPUT mode.".format(p))
        except Exception as e:
            logger.error("Error setting port={} in OUTPUT mode".format(p))
            logger.exception(e)


def init_app():
    # set the GPIO pins in output mode
    set_IO_pins()
    # endpoints
    api.add_resource(RaspberryPiServer, '/lights')
    api.add_resource(LightTimer, '/timer')


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p', type=int, default=5000, help="Server listening port")
    parser.add_argument('--debug', action='store_true', help="Whether to use Flask in debug mode")
    return parser.parse_args()


if __name__ == "__main__":

    args = get_args()

    init_app()
    app.run(host='0.0.0.0', port=args.port, debug=args.debug)


