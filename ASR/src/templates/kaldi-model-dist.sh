#!/usr/bin/env bash

# set -e
# set -o pipefail

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

echo
echo
say @cyan[["========= Starting processing with KLADI-MODEL-DIST template ============"]]


if [ $# != 1 ] ; then
    echo "usage: $0 <model>"
    exit 2
fi

MODEL=$1

EXPNAME=adapt
EXPDIR="exp"

AMNAME="kaldi-${MODEL}-${EXPNAME}"

say @yellow[["Adaptation Model Name: $AMNAME ..."]]
say @yellow[["Current dir: $PWD"]]

rm -rf "$AMNAME"

say @cyan[["1. copying $EXPDIR/$EXPNAME/* to $AMNAME/model/"]]
mkdir -p "$AMNAME/model"

cp $EXPDIR/$EXPNAME/final.mdl                               $AMNAME/model/
cp $EXPDIR/$EXPNAME/final.mat                               $AMNAME/model/ # 2>/dev/null
cp $EXPDIR/$EXPNAME/final.occs                              $AMNAME/model/ # 2>/dev/null
cp $EXPDIR/$EXPNAME/full.mat                                $AMNAME/model/ # 2>/dev/null
cp $EXPDIR/$EXPNAME/splice_opts                             $AMNAME/model/ # 2>/dev/null
cp $EXPDIR/$EXPNAME/cmvn_opts                               $AMNAME/model/ # 2>/dev/null
cp $EXPDIR/$EXPNAME/tree                                    $AMNAME/model/ # 2>/dev/null


say @cyan[["2. copying $EXPDIR/$EXPNAME/graph/* to $AMNAME/model/graph"]]
mkdir -p "$AMNAME/model/graph"

cp $EXPDIR/$EXPNAME/graph/HCLG.fst                          $AMNAME/model/graph/
cp $EXPDIR/$EXPNAME/graph/words.txt                         $AMNAME/model/graph/
cp $EXPDIR/$EXPNAME/graph/num_pdfs                          $AMNAME/model/graph/
cp $EXPDIR/$EXPNAME/graph/phones.txt                        $AMNAME/model/graph/


say @cyan[["3. copying $EXPDIR/$EXPNAME/graph/phones/* to $AMNAME/model/graph/phones"]]
mkdir -p "$AMNAME/model/graph/phones"
cp $EXPDIR/$EXPNAME/graph/phones/*                          $AMNAME/model/graph/phones/

if [ -e $EXPDIR/extractor/final.mat ] ; then

    say @magenta[["4.1. copying $EXPDIR/extractor/* to $AMNAME/extractor"]]
    mkdir -p "$AMNAME/extractor"

    cp $EXPDIR/extractor/final.mat                          $AMNAME/extractor/
    cp $EXPDIR/extractor/global_cmvn.stats                  $AMNAME/extractor/
    cp $EXPDIR/extractor/final.dubm                         $AMNAME/extractor/
    cp $EXPDIR/extractor/final.ie                           $AMNAME/extractor/
    cp $EXPDIR/extractor/splice_opts                        $AMNAME/extractor/

    say @magenta[["4.2. copying $EXPDIR/ivectors_test_hires/conf/* to $AMNAME/ivectors_test_hires/conf"]]
    mkdir -p "$AMNAME/ivectors_test_hires/conf"

    cp $EXPDIR/ivectors_test_hires/conf/ivector_extractor.conf  $AMNAME/ivectors_test_hires/conf/
    cp $EXPDIR/ivectors_test_hires/conf/online_cmvn.conf        $AMNAME/ivectors_test_hires/conf/
    cp $EXPDIR/ivectors_test_hires/conf/splice.conf             $AMNAME/ivectors_test_hires/conf/

fi


say @cyan[["5. copying data/local/dict/* to $AMNAME/data/local/dict/"]]
mkdir -p "$AMNAME/data/local/dict"
cp data/local/dict/*     $AMNAME/data/local/dict/

cp -rp data/lang         $AMNAME/data/


say @cyan[["6. copying conf/* to $AMNAME/conf/"]]
mkdir -p "$AMNAME/conf"
cp conf/mfcc.conf        $AMNAME/conf/mfcc.conf
cp conf/mfcc_hires.conf  $AMNAME/conf/mfcc_hires.conf
cp conf/online_cmvn.conf $AMNAME/conf/online_cmvn.conf

rm -f "$AMNAME.tar" "$AMNAME.tar.xz"
tar cfv "$AMNAME.tar" $AMNAME
xz -v -8 -T 12 "$AMNAME.tar"

rm -r "$AMNAME"

