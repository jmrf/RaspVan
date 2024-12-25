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
         -e "s/@magenta/$(tput setaf 5)/g" \
         -e "s/@cyan/$(tput setaf 6)/g" \
         -e "s/@white/$(tput setaf 7)/g" \
         -e "s/@reset/$(tput sgr0)/g" \
         -e "s/@b/$(tput bold)/g" \
         -e "s/@u/$(tput sgr 0 1)/g"
}


# check current directory
current_dir=${PWD##*/}
if [ "$current_dir" == "scripts" ]; then
    cprint @red[["This scripts should be executed from the root folder as: ./scripts/download_binaries.sh"]]
    exit
fi

ARCH=$(uname -m)

cprint @yellow[["🚧 WARNING: This will download an older version (v0.1.1) of the precise-runner!"]]
cprint @yellow[["🚧 WARNING: To get the latest (v0.3.1) you need to compile from source:"]]
cprint @yellow[["🛠️  https://github.com/josemarcosrf/mycroft-precise#source-install"]]
ENGINE_TAR_URI="https://github.com/josemarcosrf/precise-data/raw/dist/$ARCH/precise-engine.tar.gz"
# ENGINE_TAR_URI="https://github.com/MycroftAI/mycroft-precise/releases/download/v0.3.0/precise-all_0.3.0_${ARCH}.tar.gz"

TAR_FILE=$(echo $ENGINE_TAR_URI | awk -F'/' '{print $NF}')
if [ ! -f $TAR_FILE ]; then
    cprint @blue[["⏬ Downloading binaries for '$ARCH'"]]
    wget $ENGINE_TAR_URI
fi

if [ -f $TAR_FILE ]; then
    cprint @blue[["📚️ Extracting binaries..."]]
    tar -xvf $TAR_FILE
    rm -r $TAR_FILE
fi

cprint @magenta[["precise-engine version: "]]
$(precise/precise-engine --version)

