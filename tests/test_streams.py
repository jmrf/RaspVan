import time
from pyaudio import PyAudio, paInt16


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
                rate=48000,
                channels=1,
                format=paInt16,
                input=True,
                # frames_per_buffer=2048,
                input_device_index=0,
            )
            streams.append(stream)
            n = len(streams)
            print(f"Total number of streams: {n} (channels={n*4})")
            time.sleep(1)

        assert len(streams) == i + 1

    except Exception as e:
        print(f"Error: {e}")
    finally:
        close(pa, streams)

    print("👋 bye!")
