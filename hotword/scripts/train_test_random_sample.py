import argparse
import random
import os
import glob
import shutil


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("label", required=True, help="The wake-word directory name")

    return parser.parse_args()


if __name__ == "__main__":

    args = get_args()

    data_path = f"./data/{args.label}/wake-word"
    test_data_path = f"./data/{args.label}/test/wake-word"

    all_recordings = glob.glob(os.path.join(data_path, "*.wav"))

    print(f"Found: {len(all_recordings)}")

    random.shuffle(all_recordings)

    test_idx = int(0.2 * len(all_recordings))
    test_recordings = all_recordings[:test_idx]

    for rec in test_recordings:
        shutil.move(rec, os.path.join(test_data_path, os.path.basename(rec)))
