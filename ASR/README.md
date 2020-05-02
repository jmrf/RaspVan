# STT (Speech To Text) / ASR (Automatic Speech Recognition)


The goal of an STT system is to transcribe from an audio stream the most likely
sequence of words from an accoustic observation.


If you do not know where to begin at,
[this video series](https://www.youtube.com/watch?v=i9Gn2QYrYpo) could be a great start.

In a nutshell `Automatic Speech Recognition` requires different type of models,
working one after the other to be able to transform a soundwave into text.

The main components are:

- Acoustic model: Mapping accoustic observations
- Lexicons or Dictionaries: Defining the possible **words** in the domain of application
- Grapheme-to-Phoneme (G2P): Mapping words to **pronunciations**
- Language Model: Mapping sequence of word probabilities to sentences or phrases.

All these componentes together define what we call a **ASR** model.

However, new advances have been making increasingly possible to have end-to-end
systems.


Table of Contents
=================

   * [ASR (Automatic Speech Recognition)](#asr-automatic-speech-recognition)
   * [Table of Contents](#table-of-contents)
      * [Requirements](#requirements)
      * [Frameworks](#frameworks)
         * [Tools](#tools)
      * [Install](#install)
      * [Training](#training)
      * [Inference](#inference)
         * [wav2letter](#wav2letter)
         * [Kaldi](#kaldi)

Created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc)


## Requirements

- python >= 3.6
- [kenLM](https://github.com/kpu/kenlm) (only if training a new language model)

In addition, we will be using one of the below frameworks.

## Frameworks

We consider a few different options for the `ASR` pipeline:

* [wav2letter](https://github.com/facebookresearch/wav2letter/)
* [Kaldi](https://kaldi-asr.org/): To begin understanding `Kaldi` a good place
    to start from is the
    [4 part kaldi lectures](https://sites.google.com/site/dpovey/kaldi-lectures).

To see how this frameworks compare, check this
[funny article](https://mc.ai/how-fast-is-facebooks-end-to-end-speech-recognition-toolkit/)

### Tools

* aerecord
* aplay
* sox


## Install

Only necessary if we want to train a language model. Assuming Ubuntu OS:

Install dependencies and packages:
```bash
sudo apt install build-essential cmake \
    libboost-system-dev libboost-thread-dev \
    libboost-program-options-dev libboost-test-dev \
    libeigen3-dev zlib1g-dev libbz2-dev liblzma-dev
```

Install `kenLM` ([build instructions](https://github.com/kpu/kenlm/blob/master/BUILDING)):

```bash
# clone the repo
cd external && git clone https://github.com/kpu/kenlm.git
# install
cd kenlm && mkdir -p build && cd build
  cmake ..
  make -j 4

```


## Training

Potentially a pre-trained ASR model could be enough. However, adapting the
`language model` to the specific domain should yield better results.

This can be done as follows:

```
    # 1. Run the data preparation scripts
    ./prepare_lm_data.sh

    # 2. train the language model
    ./train_lm.sh

    # 3. Start the ASR model adaptation
    python -m src.adapt -h
```


## Inference

### wav2letter

For inference we can use the
[dockerized inference pipeline](https://github.com/facebookresearch/wav2letter/wiki/Building-Running-with-Docker)

```
docker run --rm -it \
    -v ${PWD}/data:/data \
    --ipc=host \
    --name w2l \
    wav2letter/wav2letter:inference-latest
```

**TODO**: Make a custom image with all of this ready!

Once inside we can do some preparation to simplify things inside the container:

```
# create a softling to wav2letter binaries
cd bin && \
ln -s /root/wav2letter/build/inference/inference/examples/multithreaded_streaming_asr_example streaming_asr && \
ln -s /root/wav2letter/build/inference/inference/examples/interactive_streaming_asr_example interactive_asr

# download pre-trained models
cd / && mkdir model && cd / model && \
for f in acoustic_model.bin tds_streaming.arch decoder_options.json feature_extractor.bin language_model.bin lexicon.txt tokens.txt ; do wget http://dl.fbaipublicfiles.com/wav2letter/inference/examples/model/${f} ; done

```

Once this is done we can record wav files to test:

```
    arecord -f S16_LE -r 16000 -D default -c 1 my_wav_redcording.wav
```

Copying them to the `./data` folder we mounted in the container will allow
as to test the models:

```
    # start the interactive ASR
    interactive_asr --input_files_base_path /model
    # ...
    Entering interactive command line shell. enter '?' for help.
    ------------------------------------------------------------
    $>input=/data/my_wav_redcording.wav

```



For details check:
[docker inference](https://github.com/facebookresearch/wav2letter/wiki/Inference-Run-Examples#Quickly-run-Streaming-ASR-Examples-using-Docker)



### Kaldi


Once we have a clear idea of how this works, we can start with the following two components:

 * [Kaldi ASR](https://github.com/kaldi-asr/kaldi)
 * [py-kaldi-asr](https://github.com/gooofy/py-kaldi-asr)

We can start with one of these dockerized
[kaldi ASR pre-trained models](https://quay.io/repository/mpuels/docker-py-kaldi-asr-and-model?tab=tags)

And use this [client](https://github.com/mpuels/docker-py-kaldi-asr-and-model)
to send audio to it

To start the STT service on your local machine, execute:
```
    docker pull quay.io/mpuels/docker-py-kaldi-asr-and-model:kaldi-generic-en-tdnn_250-r20180815
    docker run --rm -p 127.0.0.1:8080:80/tcp \
        quay.io/mpuels/docker-py-kaldi-asr-and-model:kaldi-generic-en-tdnn_250-r20180815
```

To transfer an audio file for transcription to the service, in a second
terminal, execute:
```
    conda env create -f environment.yml
    source activate py-kaldi-asr-client
    ./asr_client.py asr.wav
```


