import argparse
import asyncio
import glob
import os

from halo.halo import Halo

from asr.client import ASRClient


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir")
    parser.add_argument("--glob-mask", "-m", default="*.wav")
    parser.add_argument("--asr-server-uri", "-u", default="ws://localhost:2700")

    return parser.parse_args()


async def wav_to_text(asr_uri: str, wav_file: str):
    client = ASRClient(asr_uri, vad=None)
    res = await client.from_wave(wav_file)

    return res["text"]


if __name__ == "__main__":
    args = get_args()

    wav_files = glob.glob(os.path.join(args.data_dir, args.glob_mask))
    for wav_file in wav_files:
        fname = os.path.basename(wav_file)
        with Halo(f"Processing: {fname}") as sp:
            res = asyncio.run(wav_to_text(args.asr_server_uri, wav_file))
            sp.succeed()

        print(res)
