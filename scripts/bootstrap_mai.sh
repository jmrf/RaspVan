#!/usr/bin/env bash

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
    say @red[["This scripts should be executed from the root folder as: ./scripts/bootstrap_mai.sh"]]
    exit
fi


if [ -z "$1" ]; then
    CONF="./mai_engine/config/config.yml"
else
    CONF=$1
fi

if [ -z "$2" ]; then
    say @blue[["Setting TENSORFLOW num threads = 4"]]
    OMP_NUM_THREADS=4
else
    say @blue[["Setting TENSORFLOW num threads = $2"]]
    OMP_NUM_THREADS=$2
fi

say @green[["Training model using conf. file: $CONF "]]

model_name="model-$(date --iso-8601=minutes)"

{
  rasa train \
    --data ./mai_engine/data/train/ \
    --domain ./mai_engine/config/domain.yml \
    --config $CONF \
    --out mai_engine/models/ \
    --fixed-model-name $model_name \
    --verbose;
    rm ./mai_engine/models/current.tar.gz
    ln -s $model_name.tar.gz  ./mai_engine/models/current.tar.gz
} || {
  say @red[["Couldn't train a MAI model...exiting"]];
  exit 1;
}
