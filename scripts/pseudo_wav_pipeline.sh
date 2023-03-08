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
         -e "s/@magenta/$(tput setaf 2)/g" \
         -e "s/@cyan/$(tput setaf 6)/g" \
         -e "s/@white/$(tput setaf 7)/g" \
         -e "s/@reset/$(tput sgr0)/g" \
         -e "s/@b/$(tput bold)/g" \
         -e "s/@u/$(tput sgr 0 1)/g"
}

# We first need the asr-server service running:
# > docker-compose up -d asr-server
#
# Second; we can run the ASRClient from wav files:
say @cyan[["Processing converting wav files to text..."]]
python -m scripts.wav_to_text \
    ./data/recordings-for-nlu/ \
    | grep -v Processing | sed 's/\r//' | grep . > out

# Third; We run the NLU service from docker mounting the NLU module as mount volume
#       (uses a different numpy version so we run it containerized)
#
# Finally; We pick the last line of the NLU output and manipulate to use JQ
say @cyan[["Running NLU on each prediction..."]]
nlines=$(cat out |wc -l)
cat out | docker run -i \
        -v ${PWD}/nlu/:/app/nlu \
        -v ${PWD}/common/:/app/common \
        jmrf/nlu-rpi:0.1.0 python -m nlu.__init__ \
            | tail -n $nlines \
            | sed s/\'/\"/g \
            | jq


say @green[["Done :)"]]


