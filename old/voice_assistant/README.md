# Phiona Raspberry Voice Assistant

A simple voice assistant powered by [Snips](nips.ai) ASR.

The NLU part can either be run by `snips-nlu` or by your own `NLU` engine.
When using other `nlu` different from snips-nlu such engine should listen to the `ASR` messages published at the MQTT broker.

## Instalation

Installation consists of two parts:

* PC application manager:

* On device installation:

### Custom wakeword:

Follow the instruction found in this [repo](https://github.com/jmrf/snips-record-personal-hotword) to train and use your own wakeword.

## Deployment

## Run

### Connect to Actions: Subscribe to MQTT messages

The ASR publishes the detected information to a MQTT broker.

To read messages published after _any_ wakeword detection:
```bash
   mosquitto_sub -h localhost -p 1883 -v -t hermes/hotword/#
```

To read _voice transcription_ published messages
```bash
    mosquitto_sub -h localhost -p 1883 -v -t hermes/asr/textCaptured
```

To read specific intents (use `hermes/intent/#` to read any intent):
```bash
    mosquitto_sub -h localhost -p 1883 -v -t hermes/intent/<intent_name>
```


## Monitor:

* From application manager:
```bash
    sam watch
```

* On device:
```bash
    snips-watch
```
