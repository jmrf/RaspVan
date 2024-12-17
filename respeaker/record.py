import wave

import pyaudio

from respeaker.constants import RESPEAKER_CHANNELS, RESPEAKER_RATE, RESPEAKER_WIDTH

RESPEAKER_DEVICE_INDEX = 0  # refer to input device id

CHUNK = 1024
WAVE_OUTPUT_FILENAME = "output.wav"


def record_audio(
    record_seconds: int,
    output_filename=WAVE_OUTPUT_FILENAME,
    rate=RESPEAKER_RATE,
    channels=RESPEAKER_CHANNELS,
    width=RESPEAKER_WIDTH,
):
    p = pyaudio.PyAudio()
    stream = p.open(
        rate=rate,
        format=p.get_format_from_width(RESPEAKER_WIDTH),
        channels=channels,
        input=True,
        # input_device_index=RESPEAKER_INDEX,
    )
    print("🎙️ recording")

    frames = []
    for _ in range(int(rate / CHUNK * record_seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("🎬️ done recording")
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(output_filename, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(p.get_format_from_width(width)))
    wf.setframerate(rate)
    wf.writeframes(b"".join(frames))
    wf.close()
    print(f"🔊 saved output as: '{output_filename}'")
