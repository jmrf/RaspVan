import os
import sys
import deepspeech
import wave
import numpy as np

from common.utils.decorators import timeit

from raspvan.constants import ASR_MODEL_ENV_VAR
from raspvan.constants import ASR_SCORER_ENV_VAR


@timeit
def read_wav_file(audio_file):
    print(f"🔔 reading audio file")
    fin = wave.open(audio_file, "rb")
    fin_rate = fin.getframerate()
    audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)

    return audio, fin_rate


@timeit
def load_model():
    print(f"🧠 Loading model")
    MODEL_PATH = os.getenv(ASR_MODEL_ENV_VAR)
    SCORER_PATH = os.getenv(ASR_SCORER_ENV_VAR)

    if MODEL_PATH is None or SCORER_PATH is None:
        raise ValueError(
            "🛑 Can't load model! Make sure to to set the env.vars: "
            f"'{ASR_MODEL_ENV_VAR}' and '{ASR_SCORER_ENV_VAR}'"
        )

    model = deepspeech.Model(MODEL_PATH)
    model.enableExternalScorer(SCORER_PATH)

    return model


@timeit
def transcribe(model, audio):
    print("⚙️ Transcribing text")
    return model.stt(audio)


if __name__ == "__main__":
    # Load the model
    model = load_model()
    desired_sample_rate = model.sampleRate()

    # Read the wav file
    audio_file = sys.argv[1]
    audio, fr_orig = read_wav_file(audio_file)

    if fr_orig != desired_sample_rate:
        print(
            "⚠️ Error! "
            f"input file sample rate ({fr_orig}) != model sample rate ({desired_sample_rate})"
        )

    # STT
    text = transcribe(model, audio)
    print(f"🤓 Text: {text}")
