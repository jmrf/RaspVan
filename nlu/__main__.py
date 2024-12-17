import sys

import click

from nlu import NLUPipeline


@click.command()
@click.option("-c", "--classifier", default="nlu/models/intent-clf.pkl")
@click.option("-l", "--label-encoder", default="nlu/models/intent-le.pkl")
@click.option("-t", "--tagger", default="nlu/models/intent-tagger.pkl")
def run_pipeline(classifier, label_encoder, tagger):
    nlp = NLUPipeline(classifier, label_encoder, tagger)
    for line in sys.stdin:
        res = nlp([line.strip()])[0]
        print(f"🔮 Result: {res}")


if __name__ == "__main__":
    run_pipeline()
