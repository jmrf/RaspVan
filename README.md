# RaspVan

Domotics using a Raspberry Pi 3 for our own-built campervan.

At the moment is just a simple prototype to control the van lights
either by _voice_ or by sending _POST requests_ to a python server.



## Structure

```bash
.
├── phiona_server.py 			    # simple Flask server to control the lights through HTTP requests
├── raspberry-pi-pinout.png 		    # Raspberry GPIO pins layout
├── README.md
└── Voice assistant 		  	    # Voice assistant directory
    ├── assistantproj_rkr68ZJX-phiona.zip   # Snips voice assistant zipped model file
    ├── voice_action_server.py 		    # listens to MQTT for recognized voice commands and execute  appropiate actions
    └── run_voice_assistant.sh 		    # run dockerized voice assistant
```

## How to

To run the voice assitant:
```bash
	~./voice_assitant/run_voice_assistant.sh~
	python3 voice_action_server.py
```

To run the HTTP server:
```bash
	python3 http_server.py
```
## Wiring and Connections

* Lights:

  Connections are done from the raspberryPi GPIO pins to the _positive_ side of the lights circuit (high-side switch) using a _p-channel MOSFET_ transistor. 
  Discussion on low-side or high-side switching are out of the scope of this _readme_ document.
  ​
  An schematic view of the _switch_ mechanism follows (from this [partsim project](http://www.partsim.com/simulator#132504)):

  ![high-side switch](high-side-switch.jpeg)



### Misc

* Drawing and simulation tool: [partsim simulator](https://www.partsim.com/simulator)
