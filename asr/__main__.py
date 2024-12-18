import asyncio

import click

from asr.client import ASRClient
from asr.vad import VAD
from common import int_or_str

# Create an event loop shared between the different CLI groups
loop = asyncio.new_event_loop()

# Share the ASR client shared between the different CLI groups
ASR = None


@click.group()
@click.option(
    "-s",
    "--asr_server_uri",
    type=str,
    help="ASR Server URI",
    default="ws://localhost:2700",
)
@click.option(
    "-v", "--vad-aggressiveness", type=int, help="VAD aggressiveness", default=1
)
def cli(asr_server_uri, vad_aggressiveness):
    """Run ASR client to submit an audio file or an audio capture"""

    async def init():
        global ASR
        ASR = ASRClient(asr_server_uri, VAD(vad_aggressiveness))

    task = loop.create_task(init())
    loop.run_until_complete(task)


@cli.command()
@click.option(
    "-d",
    "--device",
    type=int_or_str,
    help="input device (numeric ID or substring)",
    default=0,
)
@click.option("-r", "--samplerate", type=int, help="sampling rate", default=16000)
def from_mic(device, samplerate):
    """Perform ASR from microphone captured audio"""

    async def stream():
        res = await ASR.stream_mic(samplerate, device)
        print(f"🎤 result: '{res}'")

    task = loop.create_task(stream())
    loop.run_until_complete(task)


@cli.command()
@click.argument("wfile", type=click.Path(dir_okay=False))
def from_wav(wfile):
    """Perform ASR on the given WAV file"""

    async def awav():
        res = await ASR.from_wave(wfile)
        print(f"🎶 result: '{res}'")

    task = loop.create_task(awav())
    loop.run_until_complete(task)


if __name__ == "__main__":
    cli()
