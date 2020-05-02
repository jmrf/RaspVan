import logging
import os
import sys
from argparse import ArgumentParser

from .kaldi_adapt import kaldi_adapt_lm

DEFAULT_KALDI_ROOT = "/opt/kaldi"
DEFAULT_MODEL_DIR = "./models/lm"
DEFAULT_WORK_DIR = "work"


def get_args():
    parser = ArgumentParser("Kaldi Language Model adaptation")

    io_group = parser.add_argument_group("i/o directory and paths")
    io_group.add_argument(
        "-k",
        "--kaldi-root",
        default=DEFAULT_KALDI_ROOT,
        help="kaldi root dir (default: %s)" % DEFAULT_KALDI_ROOT,
    )
    io_group.add_argument(
        "-m",
        "--src-model-dir",
        default=DEFAULT_MODEL_DIR,
        help="model dir (default: %s)" % DEFAULT_MODEL_DIR,
    )
    io_group.add_argument(
        "-lm", "--lm-fn", help="Language Model function (the output of kenLM)"
    )
    io_group.add_argument(
        "-w",
        "--work-dir",
        default=DEFAULT_WORK_DIR,
        help="work dir (default: %s)" % DEFAULT_WORK_DIR,
    )
    io_group.add_argument(
        "-o", "--dst-model-name", help="Output model name",
    )
    # Extra options
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        dest="force",
        help="overwrite work dir if it exists",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="enable verbose logging",
    )

    return parser.parse_args()


if __name__ == "__main__":

    args = get_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    work_dir = args.work_dir

    if os.path.exists(work_dir):
        if args.force:
            # cleanup leftovers from previous runs
            cmd = "rm -rf %s" % work_dir
            logging.info(cmd)
            os.system(cmd)
        else:
            logging.error("work dir %s already exists." % work_dir)
            sys.exit(1)

    kaldi_adapt_lm(
        args.kaldi_root, args.src_model_dir, args.lm_fn, work_dir, args.dst_model_name
    )

    logging.info("All done.")
