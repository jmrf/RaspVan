import logging
import os
import subprocess

from .misc import configure_logging
from .misc import copy_file
from .misc import mkdirs
from .misc import render_template
from .misc import symlink

logger = logging.getLogger(__name__)
configure_logging(logger, level=logging.DEBUG)


def kaldi_adapt_lm(kaldi_root, src_model_dir, lm_fn, work_dir, dst_model_name):

    steps_path = "%s/egs/wsj/s5/steps" % kaldi_root
    if not os.path.exists(steps_path):
        raise Exception(
            "%s does not exist - is kaldi really installed in %s ?"
            % (steps_path, kaldi_root)
        )

    tmpl_dir = os.path.dirname(os.path.abspath(__file__)) + "/templates"

    #
    # copy dictionary and phoneme sets from original model
    #

    logger.info("copying dictionary and phoneme sets from original model...")

    mkdirs("%s/data/local/dict" % work_dir)
    copy_file(
        "%s/data/local/dict/lexicon.txt" % src_model_dir,
        "%s/data/local/dict/lexicon.txt" % work_dir,
    )
    copy_file(
        "%s/data/local/dict/nonsilence_phones.txt" % src_model_dir,
        "%s/data/local/dict/nonsilence_phones.txt" % work_dir,
    )
    copy_file(
        "%s/data/local/dict/silence_phones.txt" % src_model_dir,
        "%s/data/local/dict/silence_phones.txt" % work_dir,
    )
    copy_file(
        "%s/data/local/dict/optional_silence.txt" % src_model_dir,
        "%s/data/local/dict/optional_silence.txt" % work_dir,
    )
    copy_file(
        "%s/data/local/dict/extra_questions.txt" % src_model_dir,
        "%s/data/local/dict/extra_questions.txt" % work_dir,
    )

    #
    # language model
    #

    copy_file(lm_fn, "%s/lm.arpa" % work_dir)

    #
    # create skeleton dst model
    #

    logger.info("creating skeleton destination model...")

    mkdirs("%s/exp/adapt" % work_dir)

    copy_file("%s/model/final.mdl" % src_model_dir, "%s/exp/adapt/final.mdl" % work_dir)
    copy_file("%s/model/cmvn_opts" % src_model_dir, "%s/exp/adapt/cmvn_opts" % work_dir)
    copy_file("%s/model/tree" % src_model_dir, "%s/exp/adapt/tree" % work_dir)

    for optional_file in ["final.mat", "splice_opts", "final.occs", "full.mat"]:
        if os.path.exists(f"{src_model_dir}/model/{optional_file}"):
            copy_file(
                f"{src_model_dir}/model/{optional_file}",
                f"{work_dir}/exp/adapt/{optional_file}",
            )

    if os.path.exists("%s/extractor" % src_model_dir):

        mkdirs("%s/exp/extractor" % work_dir)

        copy_file(
            "%s/extractor/final.mat" % src_model_dir,
            "%s/exp/extractor/final.mat" % work_dir,
        )
        copy_file(
            "%s/extractor/global_cmvn.stats" % src_model_dir,
            "%s/exp/extractor/global_cmvn.stats" % work_dir,
        )
        copy_file(
            "%s/extractor/final.dubm" % src_model_dir,
            "%s/exp/extractor/final.dubm" % work_dir,
        )
        copy_file(
            "%s/extractor/final.ie" % src_model_dir,
            "%s/exp/extractor/final.ie" % work_dir,
        )
        copy_file(
            "%s/extractor/splice_opts" % src_model_dir,
            "%s/exp/extractor/splice_opts" % work_dir,
        )

        mkdirs("%s/exp/ivectors_test_hires/conf" % work_dir)

        copy_file(
            "%s/ivectors_test_hires/conf/splice.conf" % src_model_dir,
            "%s/exp/ivectors_test_hires/conf" % work_dir,
        )
        copy_file(
            "%s/ivectors_test_hires/conf/ivector_extractor.conf" % src_model_dir,
            "%s/exp/ivectors_test_hires/conf" % work_dir,
        )
        copy_file(
            "%s/ivectors_test_hires/conf/online_cmvn.conf" % src_model_dir,
            "%s/exp/ivectors_test_hires/conf" % work_dir,
        )

    mkdirs("%s/conf" % work_dir)
    copy_file("%s/conf/mfcc.conf" % src_model_dir, "%s/conf/mfcc.conf" % work_dir)
    copy_file(
        "%s/conf/mfcc_hires.conf" % src_model_dir, "%s/conf/mfcc_hires.conf" % work_dir
    )
    copy_file(
        "%s/conf/online_cmvn.conf" % src_model_dir,
        "%s/conf/online_cmvn.conf" % work_dir,
    )

    #
    # copy scripts and config files
    #

    copy_file(
        "%s/kaldi-run-adaptation.sh" % tmpl_dir, "%s/run-adaptation.sh" % work_dir
    )
    copy_file("%s/kaldi-cmd.sh" % tmpl_dir, "%s/cmd.sh" % work_dir)
    render_template(
        "%s/kaldi-path.sh.template" % tmpl_dir,
        "%s/path.sh" % work_dir,
        kaldi_root=kaldi_root,
    )
    copy_file("%s/kaldi-model-dist.sh" % tmpl_dir, "%s/model-dist.sh" % work_dir)

    symlink("%s/egs/wsj/s5/steps" % kaldi_root, "%s/steps" % work_dir)
    symlink("%s/egs/wsj/s5/utils" % kaldi_root, "%s/utils" % work_dir)

    try:
        cmd = '/bin/bash -c "pushd %s && bash run-adaptation.sh && popd"' % work_dir
        logger.info(cmd)
        subprocess.Popen(cmd, shell=True).wait()
    except Exception as e:
        logger.error(f"Error running 'run-adaptation.sh'!")
        logger.exception(e)
        exit(1)

    try:
        cmd = '/bin/bash -c "pushd {} && bash model-dist.sh "{}" && popd"'.format(
            work_dir, dst_model_name,
        )
        logger.info(cmd)
        subprocess.Popen(cmd, shell=True).wait()
    except Exception as e:
        logger.error(f"Error running 'model-dist.sh'!")
        logger.exception(e)
        exit(1)
