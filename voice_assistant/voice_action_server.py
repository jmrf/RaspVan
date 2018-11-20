import paho.mqtt.client as mqtt
import argparse
import datetime
import logging
import pprint
import json

from tendo import colorer

# TODO: Update to use hermes_python instead of the low level mqtt library

# TODO: Update Hermes MQTT message:
# more info: 
# https://snips.gitbook.io/documentation/console/actions/code-your-action/listening-to-intents-over-mqtt-using-javascript#the-hermes-protocol)
# main messages:
# wakeword: hermes/hotword/<hotword_id>detected
# textCaptures: hermes/asr/textCaptured
# intentDetection: hermes/intent/<intent_name>  (maybe we prefer to use our own NLU...let's see)


# lights to pin layout
MAIN_LIGHTS_PIN = 7

# GPIO imports
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(MAIN_LIGHTS_PIN, GPIO.OUT)	# map to physical ports


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def time_now():
    return datetime.datetime.now().strftime('%H:%M:%S.%f')

# MQTT client to connect to the bus
mqtt_client = mqtt.Client()

# define the name intents
TURN_LIGHTS_ON = 'hermes/intent/jmrf:TurnOnLights'
TURN_LIGHTS_OFF = 'hermes/intent/jmrf:TurnOffLights'
DIM_LIGHTS = 'hermes/intent/jmrf:DimLights'
ASSISTANT_MSG = 'hermes/tts/say'


def on_connect(client, userdata, flags, rc):
    # subscribe to Intent messgaes
    mqtt_client.subscribe(TURN_LIGHTS_ON)
    mqtt_client.subscribe(TURN_LIGHTS_OFF)
    # subscribe to informative messages
    mqtt_client.subscribe(ASSISTANT_MSG)


def get_prob(payload):
        return payload.get('intent').get('probability')


# Process a message as it arrives
def on_message(client, userdata, msg):
    try:
        # payload contains all the captured information from the ASR
        payload = json.loads(msg.payload.decode("utf-8"))
        logger.debug("Message payload: {}".format(pprint.pformat(payload)))

        # message topic corresponds to the MQTT topic, which contains the intent-name
        topic = msg.topic
        logger.info("Message topic: {}".format(topic.split("/")[-1]))

        light_type = [s['rawValue'] for s in payload.get('slots', [])
                      if s['slotName'] == 'LightType'] or '???'

        if msg.topic == TURN_LIGHTS_ON:
            logger.info(("Understood should turn on the {} lights."
                         " (prob: {:.3f})").format(light_type, get_prob(payload)))
            GPIO.output(MAIN_LIGHTS_PIN, GPIO.HIGH)
        elif msg.topic == TURN_LIGHTS_OFF:
            logger.info(("Understood should turn off the {} lights."
                         " (prob: {:.3f})").format(light_type, get_prob(payload)))
            GPIO.output(MAIN_LIGHTS_PIN, GPIO.LOW)
        elif msg.topic == DIM_LIGHTS:
            logger.info(("Understood should dim the {} lights."
                         " (prob: {:.3f})").format(light_type, get_prob(payload)))
        elif msg.topic == ASSISTANT_MSG:
            logger.info("Assistant says: '{}'".format(payload.get('text')))
    except Exception as e:
        logger.error("Error @ 'on_message': {}".format(e))
        logger.exception(e)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mqtt_server", default="localhost", help="MQTT server address")
    parser.add_argument("--mqtt_port", default=1883, help="MQTT server port")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(args.mqtt_server, args.mqtt_port)
    mqtt_client.loop_forever()
