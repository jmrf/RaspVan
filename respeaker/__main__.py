import time

import click
import pyaudio
from rich.console import Console
from rich.table import Table

from common.utils.context import no_alsa_err
from respeaker.pixels import Pixels
from respeaker.record import record_audio


@click.group("respeaker")
def cli():
    "Respeaker CLI utilities"


@cli.command()
def print_audio_devices():
    """Discover and print a table of available Audio Devices"""
    table = Table(title="Available Audio Devices")
    table.add_column("Index", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Max Input Channels", justify="right", style="green")
    table.add_column("Max Output Channels", justify="right", style="green")

    with no_alsa_err():
        pyaudio_instance = pyaudio.PyAudio()
        for i in range(pyaudio_instance.get_device_count()):
            dev = pyaudio_instance.get_device_info_by_index(i)
            name = dev["name"]  # .encode("utf-8")
            table.add_row(
                str(i),
                name,
                str(dev["maxInputChannels"]),
                str(dev["maxOutputChannels"]),
            )

        console = Console()
        console.print(table)
        console.print("\nDefault input device:")
        console.print(pyaudio_instance.get_default_input_device_info())
        console.print("\nDefault output device:")
        console.print(pyaudio_instance.get_default_output_device_info())


@cli.command()
def pixels():
    pixels = Pixels()
    while True:
        try:
            print("🌞 wakeup...")
            pixels.wakeup()
            time.sleep(3)
            print("🤔 think...")
            pixels.think()
            time.sleep(3)
            print("🗣️  speak...")
            pixels.speak()
            time.sleep(6)
            print("👋 off...")
            pixels.off()
            time.sleep(3)
        except KeyboardInterrupt:
            break
        finally:
            pixels.off()
            time.sleep(1)


@cli.command()
@click.option("-t", "--recording-seconds", type=int, default=5)
@click.option("-o", "--output_wav_filepath", type=click.Path, default="output.wav")
def record(recording_seconds, output_wav_filepath):
    record_audio(recording_seconds, output_wav_filepath)


if __name__ == "__main__":
    cli()
