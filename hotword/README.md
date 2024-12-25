# Hotword detection

We use a custom [mycroft/precise fork](https://github.com/josemarcosrf/mycroft-precise) for hot-word detection.

We collect some recordings and [train a custom word](https://github.com/josemarcosrf/mycroft-precise/wiki/Training-your-own-wake-word)by combining with [public sounds](http://pdsounds.tuxfamily.org/).

We find that collecting the following samples yields acceptable results:

- train: ~20 positive examples and ~300 negative
- test:  ~10 positive examples and ~70 negative

-----

## Table of Contents

<!--ts-->
- [Hotword detection](#hotword-detection)
  - [Table of Contents](#table-of-contents)
  - [Requirements](#requirements)
  - [Structure](#structure)
  - [How To](#how-to)
    - [Install](#install)
    - [Train a custom hotword](#train-a-custom-hotword)

<!-- Added by: jose, at: vie 24 mar 2023 22:54:28 CET -->
<!--te-->

## Requirements

- python == 3.7 (for example through `pyenv`)
- [mycroft/precise](https://github.com/josemarcosrf/mycroft-precise#source-install)

> ‼️ Important:
> Ensure `h5py==2.10.0` otherwise keras will fail to load models

> ‼️ Important:
> To train the wake-word model ensure `numpy==1.16.0

> ‼️ Important:
> Ensure you have version `0.3.0` of both `mycroft-precise` and `precise-runner`
> check with `pip list |grep precise` and `pip list |grep h5py`

## Structure

```shell
.
├── data
│   ├── phiona
│   │   ├── not-wake-word
│   │   │   └── generated
│   │   ├── test
│   │   │   ├── not-wake-word
│   │   │   │   └── generated
│   │   │   └── wake-word
│   │   └── wake-word
│   └── random
│       ├── mp3
│       ├── otherformats
│       ├── psounds
│       └── wavs
├── logs
│   ├── phiona.logs
│   └── phiona-om.logs
└── models

18 directories
```

## How To

### Install

To train a `custom model` we need to install from source.

In the `workstation` run the following to install the system dependencies, create a virtual environment and install the entire python precise package locally.

```shell
    # Build from source: Ensure there's a Python 3.7 avaialble to run the setup & install
    git clone https://github.com/josemarcosrf/mycroft-precise
    cd mycroft-precise
    ./setup.sh
```

In the `RaspberryPi`, we can use the `precise-engine` (inference) binary installs:

```shell
    ARCH=armv7l
    wget https://github.com/josemarcosrf/precise-data/raw/dist/$ARCH/precise-engine.tar.gz
    tar xvf precise-engine.tar.gz
```

And finally:

```shell
    pip install precise-runner
```

### Train a custom hotword

1. Create the appropiate data folder structures with:

```shell
bash ./scripts/crate_dirs.sh
```

2. Follow the [this wiki instructions](https://github.com/josemarcosrf/mycroft-precise/wiki/Training-your-own-wake-word#how-to-train-your-own-wake-word)

<details>
  <summary>Additional instructions. Click to expand!</summary>

======================== In the Raspeberry Pi ========================

1. Collect audio samples

```bash
cd fiona-rpi/wake-word/
./hotword/mycroft-precise/.venv/bin/precise-collect -c 4
```

======================== In the work-station ========================

2. Train the hotword model

```bash
# The firt train
precise-train -e 60 models/fiona/fiona.net fiona-rpi/

# Incremental taining
precise-train-incremental models/fiona/fiona.net fiona-rpi/ -r data/random/
```

</details>
