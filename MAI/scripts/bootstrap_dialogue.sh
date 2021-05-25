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
    say @red[["This scripts should be executed from the root folder as: ./scripts/bootstrap_dialogue.sh"]]
    exit
fi

model_name="dialogue-$(date --iso-8601=minutes).tar.gz"

# train dialogue engine
{
  rasa train core \
    --config ./mai_engine/config/config.yml \
    --stories ./mai_engine/data/train/dialogue \
    --out ./mai_engine/models \
    --domain ./mai_engine/config/domain.yml \
    --fixed-model-name $model_name \
    --debug-plots \
    --debug;
  rm ./mai_engine/models/current-core.tar.gz
  ln -s $model_name.tar.gz  ./mai_engine/models/current-core.tar.gz;
} || {
  say @red[["Couldn't train a Dialogue Engine model...exiting"]];
  exit 1;
}
