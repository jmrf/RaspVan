# RaspVan (codename: `Fiona`)

Domotics using a Raspberry Pi 3B for our own-built campervan.

At the moment it is _just a simple prototype_ aiming to become a
complete domotic voice-controled system.

Commands can be executed either by _voice_ or by sending _HTTP requests_ to a server.


Table of Contents
=================

   * [RaspVan](#raspvan)
   * [Table of Contents](#table-of-contents)
      * [Requirements](#requirements)
      * [Structure](#structure)
      * [How to](#how-to)
         * [Installation](#installation)
            * [WiFi and automatic hotspot](#wifi-and-automatic-hotspot)
            * [Voice Control:](#voice-control)
            * [HTTP Control (Android app or similar):](#http-control-android-app-or-similar)
            * [Web Control Panel (optional)](#web-control-panel-optional)
      * [Wiring and Connections](#wiring-and-connections)
      * [Misc](#misc)

Created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc)


## Requirements

Apart from any other requirement defined in the root or any of the sub-components we
need the follwing:

*  [Raspbian Buster](https://www.raspberrypi.org/downloads/raspbian/)
   ([installation guide](https://www.raspberrypi.org/documentation/installation/installing-images/README.md))
*  python >= 3.7
*  Docker & Docker-compose


## Structure

This repo is organized in a series of sub-components plus the main solution code
under [raspvan](raspvan/]).

To understand how to train, configure, test and run each sub-component please refer to
the individual readme files.

```bash
.
├── asr                     # ASR component (uses vosk-kaldi)
├── assets
├── common
├── config
├── data
├── docker-compose.yml
├── external
├── hotword                 # HotWord detection (uses Mycroft/Precise)
├── Makefile
├── README.md
├── requirements-dev.txt
├── requirements.txt
├── respeaker
├── scripts
├── setup.cfg
└── raspvan                 # client and server systems

```


### ASR

> ⚠️ TBD

### Hotword

> ⚠️ TBD

### Respeaker

> ⚠️ TBD


## How to

### Installation

Create a virtual environment

```bash
python3.7 -m venv .venv
source .venv/bin/activate
```

And install all the python dependencies

```bash
pip install -r requirements.txt
```


### Run

Individual components can be run independently:

 - hotword detection demo: `python -m raspvan.workers.hotword`
 - i2c relay demo: `python -m raspvan.workers.relay`
 - pixel demo: `python -m respeaker.pixels`


> ⚠️ TBD


<details>
  <summary>⚠️ Probably deprecated. Click to expand!</summary>

### WiFi and automatic hotspot

In order to communicate with the RaspberryPi we will configure it to connect to
a series of known WiFi networks when available and to create a Hotspot otherwise.

Refer to [auto-wifi-hotspot](http://www.raspberryconnect.com/network/item/330-raspberry-pi-auto-wifi-hotspot-switch-internet)
from [raspberryconnect/network](http://www.raspberryconnect.com/network).

By default the RaspberryPi will be accessible at the IP: `192.168.50.5` when the hotspot is active.


## Wiring and Connections

TBD

## Misc

* Drawing and simulation tool: [partsim simulator](https://www.partsim.com/simulator)

</details>
