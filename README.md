# RaspVan

Domotics using a Raspberry Pi 3 for our own-built campervan.

At the moment is just a simple prototype to control the van lights
either by _voice_ or by sending _POST requests_ to a python server.

This repo as it is works with `Raspbian Stretch` and `Snips version: 0.60.1`.



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

## Requirements

*  Raspbian Stretch
*  Snips
*  python3
*  MQTT (mosquitto)


## How to

The following steps assumes we are at the route of the repo directory located at `/home/pi/RaspVan`.

To run the voice assitant:
```bash

	python3 voice_assistant/voice_action_server.py
```

To run the HTTP server:
```bash
	python3 http_server.py
```

Ideally this processes should run on startup, for this we use `systemctl`.
For example to configure a _unit_ for the `voice_action_server`:

1. Create the `.service`:
    ```bash
    # voice-action_server server
    sudo vim /lib/systemd/system/voice_action_ctl.service
    ```

    With the following content:
    ```
    [Unit]
     Description=Python voice to action service
     After=multi-user.target

     [Service]
     Type=idle
     User=pi
     StandardOutput=file:/home/pi/RaspVan/logs/voice_action_server.log
     StandardError=file:/home/pi/RaspVan/logs/voice_action_server_err.log
     ExecStart=/usr/bin/python3 /home/pi/RaspVan/voice_assistant/voice_action_server.py

     [Install]
     WantedBy=multi-user.target

    ```

2. Reload the systemctl daemon:
    ```bash
	sudo systemctl daemon-reload
    ```

3. Enable the service
    ```bash
	sudo systemctl enable voice_action_ctl.service
    ```

To start manually and test proper functioning:
```bash
    sudo systemctl start voice_action_ctl   # start the service
    journalctl -u voice_action_ctl	    # show the logs
    systemctl status voice_action_ctl	    # check status of the service
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
