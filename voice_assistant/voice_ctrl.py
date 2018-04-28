import paho.mqtt.client as mqtt
import datetime
import logging
import pprint
import json

from tendo import colorer

# GPIO imports
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT)	# map to physical port 12


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def time_now():
    return datetime.datetime.now().strftime('%H:%M:%S.%f')

# MQTT client to connect to the bus
mqtt_client = mqtt.Client()

# define the name intents
TURN_LIGHTS_ON = 'hermes/intent/user_ryqs-JIGb__TornOnLights'
TURN_LIGHTS_OFF = 'hermes/intent/user_ryqs-JIGb__TurnOffLights'
DIM_LIGHTS = 'hermes/intent/user_ryqs-JIGb__DimLights'
ASSISTANT_MSG = 'hermes/tts/say'


def on_connect(client, userdata, flags, rc):
    # subscribe to Intent messgaes
    mqtt_client.subscribe(TURN_LIGHTS_ON)
    mqtt_client.subscribe(TURN_LIGHTS_OFF)
    # subscribe to informative messages
    mqtt_client.subscribe(ASSISTANT_MSG)


def get_prob(msg):
        return json.loads(msg.payload).get('intent').get('probability')


# Process a message as it arrives
def on_message(client, userdata, msg):

    payload = json.loads(msg.payload)
    logger.debug(pprint.pformat(payload))
    light_type = [s['rawValue'] for s in payload.get('slots', [])
                  if s['slotName'] == 'LightType'] or '???'

    if msg.topic == TURN_LIGHTS_ON:
        logger.info(("[{}] - Understood should turn on the {} lights."
                     " (prob: {:.3f})").format(time_now(), light_type, get_prob(msg)))
	GPIO.output(12, GPIO.HIGH)
    elif msg.topic == TURN_LIGHTS_OFF:
        logger.info(("[{}] - Understood should turn off the {} lights."
                     " (prob: {:.3f})").format(time_now(), light_type, get_prob(msg)))
	GPIO.output(12, GPIO.LOW)
    elif msg.topic == DIM_LIGHTS:
        logger.info(("[{}] - Understood should dim the {} lights."
                     " (prob: {:.3f})").format(time_now(), light_type, get_prob(msg)))
    elif msg.topic == ASSISTANT_MSG:
        logger.info("[{}] - {}".format(time_now(), json.loads(msg.payload).get('text')))


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect('localhost', 9898)
mqtt_client.loop_forever()
