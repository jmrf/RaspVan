#!/usr/bin/env bash

# exit when any command fails
set -e

cprint() {
 echo "$@" | sed \
         -e "s/\(\(@\(red\|green\|yellow\|blue\|magenta\|cyan\|white\|reset\|b\|u\)\)\+\)[[]\{2\}\(.*\)[]]\{2\}/\1\4@reset/g" \
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

# check current directory
current_dir=${PWD##*/}
if [ "$current_dir" == "scripts" ]; then
    cprint @red[["This scripts should be executed from the root folder as: ./scripts/create_dirs.sh"]]
    exit
fi

DIR="./assets"
for i in $DIR/*.mp3; do
    cprint @blue[["Converting $i..." ]];
    fn=${i##*/}
    ffmpeg -i $i -acodec pcm_s16le -ar 16000 -ac 1 -f wav $DIR/${fn%.*}.wav
done
