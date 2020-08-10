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

# check input file
input_file=$1
if [ -z ${input_file} ]; then
    say @red[["Please provide the input file path to convert"]]
    exit
fi

# check output file
output_file=$2
if [ -z ${output_file} ]; then
    say @red[["Please provide the output file path where to save the output wav file"]]
    exit
fi


say @green[["Converting $input_file and saving to: $output_file"]]
ffmpeg -i ${input_file} -acodec pcm_s16le -ac 1 -ar 16000 ${output_file}
