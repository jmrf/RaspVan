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

# ============================== Training kenLM model ==================================
echo
say @cyan[["Traning kenLM language model (4-gram word model)"]]
$KENLM_PATH/lmplz -o 4 \
    --prune 0 1 2 3 \
    --limit_vocab_file $LM_DATA_DIR/vocab.txt \
    --interpolate_unigrams 0 < $LM_DATA_DIR/lm.txt > $LM_MODEL_DIR/lm.arpa

# ============================== Adapting Kaldi ASR model ==============================
echo
say @cyan[["Adapting language model"]]
py=$(which python)

say @yellow[["python binary: $py"]]

python -m src.adapt \
    --kaldi-root $KALDI_PATH \
    -m $MODEL_DIR/$BASE_ASR_MODEL_NAME \
    -lm $LM_MODEL_DIR/lm.arpa \
    -o $DST_MODEL_NAME \
    -w $WORKDIR_PATH \
    --force --verbose

cp $WORKDIR_PATH/kaldi-$DST_MODEL_NAME-adapt.tar.xz $MODEL_DIR

say @green[["Done! :)"]]
