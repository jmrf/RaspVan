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
         -e "s/@magenta/$(tput setaf 5)/g" \
         -e "s/@cyan/$(tput setaf 6)/g" \
         -e "s/@white/$(tput setaf 7)/g" \
         -e "s/@reset/$(tput sgr0)/g" \
         -e "s/@b/$(tput bold)/g" \
         -e "s/@u/$(tput sgr 0 1)/g"
}


if [ -z $1 ]; then
    say @red[["An audio input file must be provided. Exit..."]]
    exit
fi

# Transcribe an audio file
say @blue[["running deepspeech transcription on $1"]]
res=$(deepspeech \
        --model deepspeech-0.9.3-models.pbmm \
        --scorer deepspeech-0.9.3-models.scorer \
        --audio $1)

say @magenta"==> Result:" @green "'${res}'"
