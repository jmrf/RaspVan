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

label=$1

if [ -z $label ]; then
    cprint @red[["Please provide a label for the wake-word as the first parameter to the script"]]
    exit
fi

mkdir -p ./$label/wake-word
mkdir -p ./$label/not-wake-word
mkdir -p ./$label/test/wake-word
mkdir -p ./$label/test/not-wake-word
