import asyncio
import click
import glob
import os

from halo.halo import Halo

from asr.client import ASRClient


async def wav_to_text(asr_uri: str, wav_file: str):
    client = ASRClient(asr_uri, vad=None)
    res = await client.from_wave(wav_file)

    return res["text"]


@click.command()
@click.argument("data_dir")
@click.option("-m", "--glob-mask", default="*.wav")
@click.option("-u", "--asr-server-uri", default="ws://localhost:2700")
def transform(data_dir, glob_mask, asr_server_uri):
    wav_files = glob.glob(os.path.join(data_dir, glob_mask))
    for wav_file in wav_files:
        fname = os.path.basename(wav_file)
        with Halo(f"Processing: {fname}") as sp:
            res = asyncio.run(wav_to_text(asr_server_uri, wav_file))
            sp.succeed()

        print(res)


if __name__ == "__main__":
    transform()
