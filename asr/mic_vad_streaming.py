import argparse
import logging

from datetime import datetime

import os
import deepspeech
import numpy as np

from halo import Halo

from asr import logger
from asr.audio import VADAudio


DEFAULT_SAMPLE_RATE = 16000


def get_args():
    parser = argparse.ArgumentParser(
        description="Stream from microphone to DeepSpeech using VAD"
    )

    parser.add_argument(
        "-v",
        "--vad_aggressiveness",
        type=int,
        default=3,
        help=(
            "Set aggressiveness of VAD: an integer between 0 and 3, 0 being the least "
            "aggressive about filtering out non-speech, 3 the most aggressive. "
            "Default: 3"
        ),
    )
    parser.add_argument("--nospinner", action="store_true", help="Disable spinner")
    parser.add_argument(
        "-w", "--savewav", help="Save .wav files of utterences to given directory"
    )
    parser.add_argument(
        "-f", "--file", help="Read from .wav file instead of microphone"
    )

    parser.add_argument(
        "-m",
        "--model",
        required=True,
        help=(
            "Path to the model (protocol buffer binary file, or entire "
            "directory containing all standard-named files for model)"
        ),
    )
    parser.add_argument("-s", "--scorer", help="Path to the external scorer file.")
    parser.add_argument(
        "-d",
        "--device",
        type=int,
        default=None,
        help=(
            "Device input index (Int) as listed by "
            "pyaudio.PyAudio.get_device_info_by_index(). If not provided, "
            "falls back to PyAudio.get_default_device()."
        ),
    )
    parser.add_argument(
        "-r",
        "--rate",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        help=(
            f"Input device sample rate. Default: {DEFAULT_SAMPLE_RATE}. "
            "Your device may require 44100."
        ),
    )

    return parser.parse_args()


def main(args):
    # Load DeepSpeech model
    if os.path.isdir(args.model):
        model_dir = args.model
        args.model = os.path.join(model_dir, "output_graph.pb")
        args.scorer = os.path.join(model_dir, args.scorer)

    logger.info(f"🚀 Initializing model... model: {args.model}")
    model = deepspeech.Model(args.model)
    if args.scorer:
        logging.info(f"scorer: {args.scorer}")
        model.enableExternalScorer(args.scorer)

    # Start audio with VAD
    vad_audio = VADAudio(
        aggressiveness=args.vad_aggressiveness,
        device=args.device,
        input_rate=args.rate,
        file=args.file,
    )
    logger.info("Listening (ctrl-C to exit)...")
    frames = vad_audio.vad_collector()

    # Stream from microphone to DeepSpeech using VAD
    spinner = None
    if not args.nospinner:
        spinner = Halo(spinner="line")

    stream_context = model.createStream()
    wav_data = bytearray()
    for frame in frames:
        if frame is not None:
            if spinner:
                spinner.start()
            logging.debug("streaming frame")
            stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
            if args.savewav:
                wav_data.extend(frame)
        else:
            if spinner:
                spinner.stop()
            logging.debug("end utterence")
            if args.savewav:
                vad_audio.write_wav(
                    os.path.join(
                        args.savewav,
                        datetime.now().strftime("savewav_%Y-%m-%d_%H-%M-%S_%f.wav"),
                    ),
                    wav_data,
                )
                wav_data = bytearray()
            text = stream_context.finishStream()
            logger.info("Recognized: %s" % text)
            stream_context = model.createStream()


if __name__ == "__main__":

    args = get_args()

    if args.savewav:
        os.makedirs(args.savewav, exist_ok=True)

    main(args)
