import argparse
import asyncio
import json
import logging
import webrtcvad
import websockets
import sounddevice as sd

from respeaker.pixels import pixels


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(indata))


async def stream_mic(args):

    # TODO: Make as parameters
    MAX_SECONDS_NO_VOICE = 5
    ASR_BLOCK_SIZE = 4000
    VAD_BLOCK_MS = 10
    VOICE_TH = 0.9

    asr_block_ms = ASR_BLOCK_SIZE / args.samplerate * 1000  # 250ms
    vad_block_size = int(ASR_BLOCK_SIZE * VAD_BLOCK_MS // asr_block_ms)  # 160 frames
    buffer_size = int(asr_block_ms / VAD_BLOCK_MS)

    print(asr_block_ms, vad_block_size, buffer_size)

    total_seconds_no_voice = 0
    buffer = []
    vads = []

    with sd.RawInputStream(
        samplerate=args.samplerate,
        blocksize=vad_block_size,
        device=args.device,
        dtype="int16",
        channels=1,
        callback=callback,
    ) as device:

        async with websockets.connect(args.uri) as websocket:
            await websocket.send(
                '{ "config" : { "sample_rate" : %d } }' % (device.samplerate)
            )

            pixels.speak()

            while True:
                # Blocks of size 4000 @ 16kHz are 250 ms of audio
                # we need 10,20 or 30 ms blocks for VAD so we collect smaller
                # blocks and we only send to the ASR once we collected enough
                data = await audio_queue.get()

                if len(buffer) < buffer_size:
                    # PCM data buffer
                    buffer.append(data)
                    # VAD
                    _is_speech = vad.is_speech(data, int(device.samplerate))
                    vads.append(_is_speech)

                else:
                    # Are 90% of the frames voice?
                    _is_voice = len(vads) and sum(vads) >= VOICE_TH * len(buffer)

                    # Send to ASR
                    if _is_voice:
                        pixels.think()
                        total_seconds_no_voice = 0

                        # ASR on the entire buffer
                        await websocket.send(b"".join(buffer))

                        res = json.loads(await websocket.recv())
                        if "text" in res:
                            print(f"💥 Voice detected. ASR result: {res['text']}")

                        pixels.speak()

                    else:
                        if total_seconds_no_voice >= MAX_SECONDS_NO_VOICE:
                            print("🚧 Breaking")
                            break

                        total_seconds_no_voice += asr_block_ms / 1000

                    # Reset the buffers
                    buffer = []
                    vads = []

            pixels.off()

            await websocket.send('{"eof" : 1}')
            print(f"📢: {await websocket.recv()}")


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--uri",
        type=str,
        metavar="URL",
        help="Server URL",
        default="ws://localhost:2700",
    )
    parser.add_argument(
        "-d", "--device", type=int_or_str, help="input device (numeric ID or substring)"
    )
    parser.add_argument(
        "-r", "--samplerate", type=int, help="sampling rate", default=16000
    )
    parser.add_argument(
        "-v", "--vad-aggressiveness", type=int, help="VAD aggressiveness", default=1
    )
    return parser.parse_args()


async def main():
    args = get_args()

    logging.basicConfig(level=logging.INFO)

    global audio_queue
    global loop
    global vad

    loop = asyncio.get_running_loop()
    audio_queue = asyncio.Queue()
    vad = webrtcvad.Vad(args.vad_aggressiveness)

    await stream_mic(args)


if __name__ == "__main__":
    # python -m  asr.listen_asr_vad -v 2 -d 0
    asyncio.run(main())
