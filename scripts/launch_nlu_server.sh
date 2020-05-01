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
    say @red[["This scripts should be executed from the root folder as: ./scripts/launch_nlu_server.sh"]]
    exit
fi


# server accepting requests of the form:
# curl -X POST \
#   http://localhost:9001/model/parse \
#   -H 'Content-Type: application/json' \
#   -d '{
#     "text": "Is this trip physically intense?",
# }'
rasa run \
    --enable-api \
    --model mai_engine/models/current-nlu.tar.gz \
    --port 9001 \
    --endpoints mai_engine/cibfug/local_endpoints.yml \
    --log-file ./mai_engine/logs/nlu-mai.log \
    --debug
