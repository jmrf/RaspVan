import paho.mqtt.client as mqtt
import argparse
import datetime
import logging
import pprint
import json

from tendo import colorer
import RPi.GPIO as GPIO


# TODO: Update to use hermes_python instead of the low level mqtt library


# lights to pin layout
MAIN_LIGHT_PIN = 7
L1_LIGHT_PIN = 11
L2_LIGHT_PIN = 13
L3_LIGHT_PIN = 15

# light names to PIN mapping
# TODO: Define a list of synonims for this mapping. i.e.: rear == back == L1_LIGHT_PIN
light_to_pin = {
    "back": L1_LIGHT_PIN,
    "middle": L2_LIGHT_PIN,
    "front": L3_LIGHT_PIN,
    "main": MAIN_LIGHT_PIN
}

# define the name intents
TURN_LIGHTS_ON = 'hermes/intent/jmrf:TurnOnLights'
TURN_LIGHTS_OFF = 'hermes/intent/jmrf:TurnOffLights'
DIM_LIGHTS = 'hermes/intent/jmrf:DimLights'
ASSISTANT_MSG = 'hermes/tts/say'

# GPIO mode setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(MAIN_LIGHT_PIN, GPIO.OUT)
GPIO.setup(L1_LIGHT_PIN, GPIO.OUT)
GPIO.setup(L2_LIGHT_PIN, GPIO.OUT)
GPIO.setup(L3_LIGHT_PIN, GPIO.OUT)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# logger file handler
#fh = logging.FileHandler('voice_action_server.log')
#fh.setLevel(logging.DEBUG)

# logger console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# logger formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)s - %(levelname)s - %(message)s')
#fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
#logger.addHandler(fh)
logger.addHandler(ch)

# MQTT client to connect to the bus
mqtt_client = mqtt.Client()


def time_now():
    return datetime.datetime.now().strftime('%H:%M:%S.%f')


def on_connect(client, userdata, flags, rc):
    # subscribe to Intent messgaes
    mqtt_client.subscribe(TURN_LIGHTS_ON)
    mqtt_client.subscribe(TURN_LIGHTS_OFF)
    # subscribe to informative messages
    mqtt_client.subscribe(ASSISTANT_MSG)


def get_prob(payload):
        return payload.get('intent').get('probability')



def on_message(client, userdata, msg):
    """ Executes an action (switching GPIO states) based on the intent and slots received
        trhough the MQTT.
        Messages are published by an ASR + NLU engine.
    """
    try:
        # payload contains all the captured information from the ASR
        payload = json.loads(msg.payload.decode("utf-8"))
        logger.debug("Message payload: {}".format(pprint.pformat(payload)))

        # message topic corresponds to the MQTT topic, which contains the intent-name
        topic = msg.topic
        logger.info("Message topic: {}".format(topic.split("/")[-1]))

        light_names = [s['rawValue'] for s in payload.get('slots', [])
                      if s['slotName'] == 'LightType'] or '???'

        # note: Notice that we are using a low switch relay device, hence switching on
        # requires a low signal from the GPIO pins
        # i.e.: reversed switching. ON => LOW | OFF => HIGH
        
        # Switch on intent
        if msg.topic == TURN_LIGHTS_ON:
            logger.info(("Understood should turn on the {} lights."
                         " (prob: {:.3f})").format(light_names, get_prob(payload)))
            
            for l_name in light_names:
                l_pin = light_to_pin.get(l_name, None)
                if l_pin:
                    GPIO.output(l_pin, GPIO.LOW)

        # switch off intent
        elif msg.topic == TURN_LIGHTS_OFF:
            logger.info(("Understood should turn off the {} lights."
                         " (prob: {:.3f})").format(light_names, get_prob(payload)))
            
            for l_name in light_names:
                l_pin = light_to_pin.get(l_name, None)
                if l_pin:
                    GPIO.output(l_pin, GPIO.HIGH)
        
        # Dim intent
        elif msg.topic == DIM_LIGHTS:
            logger.info(("Understood should dim the {} lights."
                         " (prob: {:.3f})").format(light_names, get_prob(payload)))
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

    logger.info("Starting voice-action service...")
    args = get_args()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(args.mqtt_server, args.mqtt_port)
    
mqtt_client.loop_forever()
