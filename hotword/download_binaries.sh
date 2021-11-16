#!/usr/bin/env bash

# exit when any command fails
set -e

say() {
 echo "$@" | sed \
         -e "s/\(\(@\(red\|green\|yellow\|blue\|magenta\|cyan\|white\|reset\|b\|u\)\)\+\)[[]\{2\}\(.*\)[]]\{2\}/\1\4@reset/g" \
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


ARCH=$(uname -a |awk '{print $12}')
TAR_FILE="precise-engine.tar.gz"


say @yellow[["🚧 WARNING: This will download an older version (v0.1.1) of the precise-runner!"]]
say @yellow[["🚧 WARNING: To get the latest (v0.3.1) you need to compile from source:"]]
say @yellow[["🛠️  https://github.com/jmrf/mycroft-precise#source-install"]]


if [ ! -f $TAR_FILE ]; then
    say @blue[["⏬ Downloading binaries for '$ARCH'"]]
    wget  https://github.com/jmrf/precise-data/raw/dist/$ARCH/precise-engine.tar.gz
fi

if [ -f $TAR_FILE ]; then
    say @blue[["📚️ Extracting binaries..."]]
    tar -xvf $TAR_FILE
    rm -r $TAR_FILE
fi

say @magenta[["precise-engine version: "]]
$(precise-engine/precise-engine --version)

