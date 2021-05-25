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

# check current directory
current_dir=${PWD##*/}
if [ "$current_dir" == "scripts" ]; then
    say @red[["This scripts should be executed from the root folder as: ./scripts/build_docker.sh"]]
    exit
fi

MACHINE_TYPE=`uname -m`
if [ ${MACHINE_TYPE} == 'x86_64' ]; then
  # 64-bit architecture
  say @blue[["Downloading miniconda 64 bits for x86"]]
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
elif [ ${MACHINE_TYPE} == 'x86_32' ]; then
  # 32-bit architecture
  say @blue[["Downloading miniconda 32 bits for x86"]]
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86.sh -O ~/miniconda.sh
elif [ ${MACHINE_TYPE} == 'armv6l' ]; then
  # 32-bit architecture
  say @blue[["Downloading berryconda 32 bits for armv6l"]]
  wget https://github.com/jjhelmus/berryconda/releases/download/v2.0.0/Berryconda3-2.0.0-Linux-armv6l.sh -O ~/miniconda.sh
elif [ ${MACHINE_TYPE} == 'armv7l' ]; then
  # 32-bit architecture
  say @blue[["Downloading miniconda 32 bits for armv7l"]]
  wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-armv7l.sh -O ~/miniconda.sh
else
    say @red["Unknown architecture: $MACHINE_TYPE for miniconda. Exiting..."]
fi

say @blue[["Installing miniconda"]]
chmod +x ~/miniconda.sh && bash ~/miniconda.sh
rm -f ~/miniconda.sh

# https://stackoverflow.com/questions/39371772/how-to-install-anaconda-on-raspberry-pi-3-model-b#56852714
conda config --add channels rpi
