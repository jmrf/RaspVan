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

download_file() {
    url=$1
    dir=$2
    file_path="$dir/$(basename -- $url)"
    if [ ! -f $file_path ]; then
        say @blue[["Downloading file to $file_path"]]
        wget --quiet -P $dir $url
    else
        say @magenta[["File '$file_path' already exists. Skipping download..."]]
    fi
}

# check current directory
current_dir=${PWD##*/}
if [ "$current_dir" != "ASR" ]; then
    say @red[["This script should be executed from the ASR folder as: ./prepare_lm_data.sh"]]
    exit
fi


say @magenta[["Sourcing .env file"]]
source .env


# Download sentences
say @cyan[["Downloading sentences for language model adaptation..."]]
mkdir -p $DATA_DIR
download_file \
    'http://goofy.zamia.org/zamia-speech/misc/sentences-en.txt.xz' \
    $DATA_DIR

say @cyan[["Extracting data..."]]
DATA_PATH="$DATA_DIR/sentences-en.txt.xz"
unxz $DATA_PATH && rm $DATA_PATH

# Download model to adapt
echo
say @cyan[["Downloading ASR model $BASE_ASR_MODEL_NAME..."]]
mkdir -p $MODEL_DIR
download_file \
    "https://goofy.zamia.org/zamia-speech/asr-models/${BASE_ASR_MODEL_NAME}.tar.xz" \
    $MODEL_DIR

say @cyan[["Extracting ASR model ${BASE_ASR_MODEL_NAME}..."]]
MODEL_PATH="$MODEL_DIR/${BASE_ASR_MODEL_NAME}"
tar xf $MODEL_PATH.tar.xz -C $MODEL_DIR && rm $MODEL_PATH.tar.xz

echo
say @cyan[["Combining language data"]]
cat $DATA_DIR/utterances.txt $DATA_DIR/utterances.txt \
    $DATA_DIR/utterances.txt $DATA_DIR/utterances.txt \
    $DATA_DIR/utterances.txt $DATA_DIR/sentences-en.txt > $DATA_DIR/lm.txt

echo
say @cyan[["Extracting model vocabulary"]]
cut -f 1 -d ' ' $MODEL_PATH/data/local/dict/lexicon.txt > $DATA_DIR/vocab.txt

say @green[["Done! :)"]]
