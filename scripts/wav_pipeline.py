import argparse
import asyncio
import glob
import os

from halo.halo import Halo

from asr.client import ASRClient
from nlu import NLUPipeline


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--glob-mask", "-m", default="*.wav")
    parser.add_argument(
        "--nlu-clf",
        "-c",
        default="./nlu/models/intent-clf.pkl",
        help="NLU Intent classifier pickle file path",
    )
    parser.add_argument(
        "--nlu-label-encoder",
        "-l",
        default="./nlu/models/intent-le.pkl",
        help="NLU label encoder pickle file path",
    )
    parser.add_argument(
        "--nlu-tagger",
        "-t",
        default="./nlu/models/entity-tagger.pkl",
        help="nlu Tagger pickle file path",
    )
    parser.add_argument("--asr-server-uri", "-u", default="ws://localhost:2700")

    return parser.parse_args()


async def pipeline(asr_uri: str, nlu: NLUPipeline, wav_file: str):
    client = ASRClient(asr_uri, vad=None)
    res = await client.from_wave(wav_file)

    return nlu(res["text"])


if __name__ == "__main__":
    args = get_args()

    nlu = NLUPipeline(args.nlu_clf, args.nlu_le, args.nlu_tagger)

    wav_files = glob.glob(os.path.join(args.data_dir, args.glob_mask))
    for wav_file in wav_files:
        fname = os.path.basename(wav_file)
        with Halo(f"Processing: {fname}") as sp:
            res = asyncio.run(pipeline(wav_file))
            sp.succed()

        print(res)
