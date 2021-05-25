# Hotword detection

We use a custom [mycroft/precise fork](https://github.com/jmrf/mycroft-precise) for hot-word detection. 

We collect some recordings and [train a custom word ](https://github.com/jmrf/mycroft-precise/wiki/Training-your-own-wake-word)by combining with [public sounds](http://pdsounds.tuxfamily.org/).

We find that collecting the following samples yields acceptable results:

- train: ~20 positive examples and ~300 negative
- test:  ~10 positive examples and ~70 negative

Table of Contents
-----------------

   * [Hotword detection](#hotword-detection)
   * [Table of Contents](#table-of-contents)
      * [Introduction](#introduction)
      * [Requirements](#requirements)
      * [Structure](#structure)
      * [How To](#how-to)
         * [Install](#install)

Created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc)


## Requirements

- python >= 3.6
- [mycroft/precise](https://github.com/jmrf/mycroft-precise#source-install)


## Structure

```
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

To train a `custom model` we need to install from source:
```
    git clone https://github.com/jmrf/mycroft-precise
    cd mycroft-precise
    ./setup.sh
```

Once deployed in the `RaspberryPi`, we can use the binary installs:
```
    ARCH=armv7l
    wget https://github.com/jmrf/precise-data/raw/dist/$ARCH/precise-engine.tar.gz
    tar xvf precise-engine.tar.gz
```

And finally:
```
    pip install precise-runner
```

### Train a custom hotword

TODO
