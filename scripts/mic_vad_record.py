import argparse
import queue
import sys
import tempfile

import sounddevice as sd
import soundfile as sf
from rich.console import Console

from common import int_or_str


console = Console()


def get_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-l",
        "--list-devices",
        action="store_true",
        help="show list of audio devices and exit",
    )
    parser.add_argument(
        "-d", "--device", type=int_or_str, help="input device (numeric ID or substring)"
    )
    parser.add_argument("-r", "--samplerate", type=int, help="sampling rate")
    parser.add_argument(
        "-c", "--channels", type=int, default=1, help="number of input channels"
    )
    parser.add_argument(
        "filename",
        nargs="?",
        metavar="FILENAME",
        help="audio file to store recording to",
    )
    parser.add_argument(
        "-t", "--subtype", type=str, help='sound file subtype (e.g. "PCM_24")'
    )

    args = parser.parse_args()

    if args.list_devices:
        console.print(sd.query_devices())
        exit(0)
    if args.samplerate is None:
        # soundfile expects an int, sounddevice provides a float:
        device_info = sd.query_devices(args.device, "input")
        args.samplerate = int(device_info["default_samplerate"])
    if args.filename is None:
        args.filename = tempfile.mktemp(prefix="rec_unlimited_", suffix=".wav", dir="")

    return args


def main():
    try:
        args = get_args()

        q = queue.Queue()

        def callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            if status:
                print(status, file=sys.stderr)
            q.put(indata.copy())

        # Make sure the file is opened before recording anything:
        with sf.SoundFile(
            args.filename,
            mode="x",
            samplerate=args.samplerate,
            channels=args.channels,
            subtype=args.subtype,
        ) as file:
            with sd.InputStream(
                samplerate=args.samplerate,
                device=args.device,
                channels=args.channels,
                callback=callback,
            ):
                console.print("#" * 80)
                console.print("press Ctrl+C to stop the recording")
                console.print("#" * 80)
                while True:
                    file.write(q.get())

    except KeyboardInterrupt:
        console.print("\nRecording finished: " + repr(args.filename))
        return
    except Exception as e:
        console.print(f"[red]Error while recrding: {e}[/red]")


if __name__ == "__main__":
    main()
