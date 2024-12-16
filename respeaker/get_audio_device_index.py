import pyaudio
from rich.console import Console
from rich.table import Table

from common.utils.context import no_alsa_err

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
            str(i), name, str(dev["maxInputChannels"]), str(dev["maxOutputChannels"])
        )

    console = Console()
    console.print(table)

    console.print("\nDefault input device:")
    console.print(pyaudio_instance.get_default_input_device_info())
    console.print("\nDefault output device:")
    console.print(pyaudio_instance.get_default_output_device_info())
