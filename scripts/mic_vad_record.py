import queue
import sys
import tempfile

import click
import sounddevice as sd
import soundfile as sf
from halo import Halo
from rich.console import Console

from asr import calc_block_ms, raw_stream_to_numpy
from asr.vad import VAD
from common import int_or_str
from respeaker.pixels import Pixels

console = Console()


def record_to_file(
    vad,
    fname: str,
    sample_rate: int,
    block_size: int,
    n_channels: int,
    audio_subtype: str,
    device: str,
    max_silence_ms: int = 1500,
):
    def _callback(indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            console.print(status, file=sys.stderr)

        q.put(bytes(indata))

    try:
        pixels = Pixels()
        q = queue.Queue()

        stop = 0
        block_ms = calc_block_ms(block_size, sample_rate)
        max_silence_blocks = int(max_silence_ms / block_ms)

        # console.print(f"block ms: {block_ms}", style="dim")
        # console.print(f"max silence blocks: {max_silence_blocks}", style="dim")

        # Make sure the file is opened before recording anything:
        with sf.SoundFile(
            fname,
            mode="x",
            samplerate=sample_rate,
            channels=n_channels,
            subtype=audio_subtype,
        ) as sfile:
            with sd.RawInputStream(
                device=device,
                channels=n_channels,
                blocksize=block_size,
                samplerate=sample_rate,
                callback=_callback,
                dtype="int16",
            ) as device:
                with Halo(f"Recoding to {fname}...\n"):
                    pixels.think()
                    while True:
                        pcm_data = q.get()

                        # check VAD
                        stop += int(not vad.is_voice(pcm_data, sample_rate))
                        if stop > max_silence_blocks:
                            pixels.off()
                            console.print("\nStopping recoding...", style="dim")
                            break

                        sfile.write(
                            raw_stream_to_numpy(pcm_data, device.dtype, device.channels)
                        )

    except KeyboardInterrupt:
        console.print("\nRecording finished: " + repr(fname))
        return


@click.command()
@click.argument("filename")
@click.option(
    "-l",
    "--list-devices",
    is_flag=True,
    help="show list of audio devices and exit",
)
@click.option(
    "-d", "--device", type=int_or_str, help="input device (numeric ID or substring)"
)
@click.option("-r", "--samplerate", type=int, default=16000, help="sampling rate")
@click.option("-c", "--channels", type=int, default=1, help="number of input channels")
@click.option("-b", "--blocksize", type=int, default=4000, help="mic stream block size")
@click.option("-t", "--subtype", type=str, help='sound file subtype (e.g. "PCM_24")')
@click.option(
    "-v", "--vad-aggressiveness", type=int, help="VAD aggressiveness", default=2
)
def main(
    filename,
    list_devices,
    device,
    samplerate,
    channels,
    blocksize,
    subtype,
    vad_aggressiveness,
):
    if list_devices:
        console.print(sd.query_devices())
        sys.exit(0)
    if samplerate is None:
        # soundfile expects an int, sounddevice provides a float:
        device_info = sd.query_devices(device, "input")
        samplerate = int(device_info["default_samplerate"])
    if filename is None:
        filename = tempfile.mktemp(prefix="rec_unlimited_", suffix=".wav", dir="")
    try:
        console.print("#" * 80)
        console.print("press Ctrl+C to stop recording", style="magenta bold")
        console.print("#" * 80)

        vad = VAD(vad_aggressiveness)
        i = 0
        while True:
            record_to_file(
                vad,
                f"{filename}-{i:03}.wav",
                samplerate,
                blocksize,
                channels,
                subtype,
                device,
            )
            i += 1

            input("Press Enter when ready to record the next audio clip\n\n")
    except KeyboardInterrupt:
        console.print("Exiting...", style="cyan")
    except Exception as e:
        console.print(f"[red]Error while recrding: {e}[/red]")
        console.print_exception()


if __name__ == "__main__":
    # python -m scripts.mic_vad_record -l  --> to list audio devices
    # or
    # python -m scripts.mic_vad_record sample -d 5 -c 4 --> to run recording
    main()
