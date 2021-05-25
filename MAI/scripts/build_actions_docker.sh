#!/usr/bin/env bash

set -e
set -o pipefail

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
    say @red[["This scripts should be executed from the root folder as: ./scripts/build_actions_docker.sh"]]
    exit
fi

if [ -z "$PROJECT" ]
  then
    say @red[["Set the environemnt variable PROJECT before running this script"]]
    exit 1;
fi

if [ -z "$1" ]; then
    say @red[["Missing DEV/FULL parameter. ex: ./build_actions_docker.sh dev 0.1"]]
    exit 1
fi

if [ -z "$2" ]; then
    say @red[["Missing tag version parameter. ex: ./build_actions_docker.sh full 0.1"]]
    exit 1
fi

MODE=$1
TAG=$2

say @green[["docker build -t ${PROJECT}-actions:${TAG}"]]
say @green[["From ./bot_actions/${MODE}Actions.Dockerfile"]]
{
    docker build -t "${PROJECT}-${MODE}-actions:$TAG" \
        -t "${PROJECT}-${MODE}-actions:latest" \
        -f "./bot_actions/${MODE}Actions.Dockerfile" \
        ./bot_actions/
} || {
  say @red[["Couldn't build Docker Actions image... exiting"]];
  exit 1;
}
