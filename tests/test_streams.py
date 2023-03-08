import time

from pyaudio import paInt16
from pyaudio import PyAudio


def close(pa, streams):
    print("Terminating 'pa' and stopping streams")
    pa.terminate()
    for stream in streams:
        stream.stop_stream()


if __name__ == "__main__":
    pa = PyAudio()
    streams = []

    try:
        for i in range(5):
            print(f"Opening stream: {i}")
            stream = pa.open(
                rate=16000,
                channels=1,
                format=paInt16,
                input=True,
            )
            streams.append(stream)
            n = len(streams)
            print(f"Total number of streams: {n} (channels={n*4})")
            time.sleep(1)

        assert len(streams) == i + 1, (
            "Can't open several streams. "
            "Make sure you are using ALSA **dsnoop** as input and default device"
        )

    except Exception as e:
        print(f"Error: {e}")
    finally:
        close(pa, streams)

    print("👋 bye!")
