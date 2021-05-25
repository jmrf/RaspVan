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
    say @red[["This scripts should be executed from the root folder as: ./scripts/eval_nlu.sh"]]
    exit
fi

if [ $# -lt 1 ]
  then
    say @red[["The script requires a 'model-name'"]]
    exit 1;
fi

rasa test nlu \
    --nlu ./mai_engine/data/test/nlu/ \
    --model ./mai_engine/models/$1 \
    --report ./mai_engine/results/$1 \
    --errors ./mai_engine/results/$1/errors.json \
    --confmat ./mai_engine/results/$1/confmat.png \
    --histogram ./mai_engine/results/$1/hist.png
