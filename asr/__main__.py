import asyncio

import click

from asr.client import ASRClient
from asr.vad import VAD
from common import int_or_str


async def asr(asr_uri, device, wfile, samplerate, vad_aggressiveness):
    """Here just to serve as an example of how to run as standalone"""
    vad = VAD(vad_aggressiveness)
    asr = ASRClient(asr_uri, vad)
    if wfile:
        res = await asr.from_wave(wfile)
    else:
        res = await asr.stream_mic(samplerate, device)

    print(f"📢: {res}")


@click.command()
@click.option(
    "-asr",
    "--asr_uri",
    type=str,
    metavar="URL",
    help="ASR Server URI",
    default="ws://localhost:2700",
)
@click.option(
    "-d",
    "--device",
    type=int_or_str,
    help="input device (numeric ID or substring)",
    default=0,
)
@click.option("-f", "--wfile", type=str, help="wave file to ASR", default=None)
@click.option("-r", "--samplerate", type=int, help="sampling rate", default=16000)
@click.option(
    "-v", "--vad-aggressiveness", type=int, help="VAD aggressiveness", default=1
)
def cli(asr_uri, device, wfile, samplerate, vad_aggressiveness):
    asyncio.run(asr(asr_uri, device, wfile, samplerate, vad_aggressiveness))


if __name__ == "__main__":
    cli()  # e.g.: python -m  asr -v 2 -d 0
