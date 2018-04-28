# RaspVan

Domotics using a Raspberry Pi 3 for our own-built campervan.

At the moment is just a simple prototype to control the van lights
either by _voice_ or by sending _POST requests_ to a python server.

## Structure

```bash
.
├── phiona_server.py 			    # simple Flask server to control the lights
├── raspberry-pi-pinout.png 		    # Raspberry GPIO pins layout
├── README.md
└── Voice assistant 		  	    # Voice assistant stuff
    ├── assistantproj_rkr68ZJX-phiona.zip   # voice assistant model
    ├── voice_ctl.py 			    # listen to MQTT for recognized voice commands
    └── run_voice_assistant.sh 		    # run dockerized voice assistant
```

## How to

To run the voice assitant:
```bash
	./voice_assitant/tun_voice_assistant.sh
	python3 voice_ctl.py
```

To run the HTTP server:
```bash
	python3 phiona_server.py
```