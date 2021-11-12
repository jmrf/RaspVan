#!/usr/bin/env bash

set -e
set -o pipefail

say() {
 echo "$@" | sed \
         -e "s/\(\(@\(red\|magenta\|yellow\|blue\|magenta\|cyan\|white\|reset\|b\|u\)\)\+\)[[]\{2\}\(.*\)[]]\{2\}/\1\4@reset/g" \
         -e "s/@red/$(tput setaf 1)/g" \
         -e "s/@green/$(tput setaf 2)/g" \
         -e "s/@yellow/$(tput setaf 3)/g" \
         -e "s/@blue/$(tput setaf 4)/g" \
         -e "s/@magenta/$(tput setaf 2)/g" \
         -e "s/@cyan/$(tput setaf 6)/g" \
         -e "s/@white/$(tput setaf 7)/g" \
         -e "s/@reset/$(tput sgr0)/g" \
         -e "s/@b/$(tput bold)/g" \
         -e "s/@u/$(tput sgr 0 1)/g"
}

mkdir -p models/

# Download pre-trained English model files
if [ ! -f models/deepspeech-0.9.3-models.pbmm ]; then
    say @blue[["⏬ Downloading deepspeech model..."]]
    cd models
    curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm
    cd -
else
    say @cyan[["✅ Deepspeech model already present. Skipping download..."]]
fi

if [ ! -f models/deepspeech-0.9.3-models.scorer ]; then
    say @blue[["⏬ Downloading deepspeech scorer..."]]cd models
    curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer
    cd -
else
    say @cyan[["✅ Deepspeech scorer already present. Skipping download..."]]
fi

# Download example audio files
if [ ! -f audio-0.9.3.tar.gz ]; then
    say @blue[["⏬ Downloading audio samples..."]]
    curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/audio-0.9.3.tar.gz
    tar xvf audio-0.9.3.tar.gz
    rm audio-0.9.3.tar.gz
    rm ._audio
else
    say @cyan[["✅ Audio samples already present. Skipping download..."]]
fi

