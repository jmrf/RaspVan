# RaspVan (codename: `Fiona`)

Domotics using a Raspberry Pi 3B for our own-built campervan.

At the moment it is _just a simple prototype_ aiming to become a
complete domotic voice-controled system.

Commands can be executed either by _voice_ or by sending _HTTP requests_ to a server.

----

## Table of Contents

<!--ts-->
* [RaspVan (codename: Fiona)](#raspvan-codename-fiona)
   * [Table of Contents](#table-of-contents)
   * [Requirements](#requirements)
   * [Structure](#structure)
      * [Hotword](#hotword)
      * [ASR](#asr)
      * [Respeaker](#respeaker)
      * [Raspvan](#raspvan)
   * [How to](#how-to)
      * [Installation](#installation)
      * [WiFi and automatic hotspot](#wifi-and-automatic-hotspot)
      * [Wiring and Connections](#wiring-and-connections)
   * [Misc](#misc)

<!-- Created by https://github.com/ekalinin/github-markdown-toc -->
<!-- Added by: pi, at: Thu 21 Apr 2022 03:58:39 PM CEST -->

<!--te-->
----

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


### Hotword

> ⚠️ TBD

```bash
python -m raspvan.workers.hotword
```

### ASR

We use the dockerized vosk-server from the
[jmrf/pyvosk-rpi](https://github.com/jmrf/pyvosk-rpi) repo.

This server listens via websocket to a `sounddevice` stream and performs STT on the fly.

> 💡 For a complete list of compatible models check:
> [vosk/models](https://alphacephei.com/vosk/models)

```bash
# Run the dockerized server
docker-compose up asr-server
```

Then, run one of the clients:

```bash
source .venv/bin/activate

# ASR from a audio wav file
python -m  asr.client -v 2 -f <name-of-the-16kHz-wav-file>

# Or ASR listening from the microphone
python -m  asr.client -v 2 -d <microphone-ID>
```

Or run the rabbitMQ-triggered `raspvan ASR worker`:

```bash
python -m raspvan.workers.asr
```


### NLU

> TBD

> 💡 It is advices to collect some voice samples and run them through ASR to use
> these as training samples for the NLU component to train it on real data.

To collect voice samples and apply ASR for the NLU, run:

```bash
# discover the audio input device to use and how many input channel are available
python -m scripts.mic_vad_record -l
# Run voice recording
python -m scripts.mic_vad_record sample.wav -d 5 -c 4
```


### Respeaker

We use [respeaker 4mic hat]() as microphone and visual feedbac with its LED array.

To run the LED pixel demo:

```bash
python -m respeaker.pixels
```


### Raspvan

This is the main module which coordinates all the different components.

 - i2c relay demo: `python -m raspvan.workers.relay`



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


### Finding the sound input device ID

First list all audio devices:

```bash
python -m respeaker.get_audio_device_index
```

You should get a table simlar to this:

```bash
┏━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Index ┃ Name     ┃ Max Input Channels ┃ Max Output Channels ┃
┡━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│     0 │ upmix    │                  0 │                   8 │
│     1 │ vdownmix │                  0 │                   6 │
│     2 │ dmix     │                  0 │                   2 │
│     3 │ default  │                128 │                 128 │
└───────┴──────────┴────────────────────┴─────────────────────┘
```

Device with **index 3**, which can handle several input and output channels,
is the one to pass to the `hotword` and `ASR` workers.

> ⚠️ ALSA won't allow for audio devices to be shared,
> i.e.: accessed simultaneously by more than one application
> when using the sound card directly. ⚠️
>
> Solution: Use the pcm devices, i.e.: plugins. Specifically the dsnoop
> (to have shared input between processes) and dmix (to have several audio outputs on one card).
>
> Copy [config/.asoundrc](config/.asoundrc) to `~./asoundrc`


<details>
  <summary>⚠️ Probably deprecated. Click to expand!</summary>

### WiFi and automatic hotspot

In order to communicate with the RaspberryPi we will configure it to connect to
a series of known WiFi networks when available and to create a Hotspot otherwise.

Refer to [auto-wifi-hotspot](http://www.raspberryconnect.com/network/item/330-raspberry-pi-auto-wifi-hotspot-switch-internet)
from [raspberryconnect/network](http://www.raspberryconnect.com/network).

By default the RaspberryPi will be accessible at the IP: `192.168.50.5` when the hotspot is active.


### Wiring and Connections

TBD


## Misc

* Drawing and simulation tool: [partsim simulator](https://www.partsim.com/simulator)

</details>
