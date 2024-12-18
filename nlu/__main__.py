import sys

import click

from nlu import NLUPipeline, train
from nlu.server import init_handler_and_run_server


@click.group()
def cli():
    """NLU pipeline (clasifier and tagger) CLI"""


@cli.command()
@click.option(
    "-c",
    "--classifier",
    type=click.Path(dir_okay=False),
    default="nlu/models/intent-clf.pkl",
)
@click.option(
    "-l",
    "--labels",
    type=click.Path(dir_okay=False),
    default="nlu/models/intent-le.pkl",
)
@click.option(
    "-t",
    "--tagger",
    type=click.Path(dir_okay=False),
    default="nlu/models/intent-tagger.pkl",
)
def run_nlu(classifier, labels, tagger):
    """Run the NLU pipeline

    Args:
        classifier (str): Path to the pickled classifier model
        labels (str): Path to the pickled label-encoder model
        tagger (str): Path to the pickled CRF tagger model
    """
    nlp = NLUPipeline(classifier, labels, tagger)
    for line in sys.stdin:
        res = nlp([line.strip()])[0]
        print(f"🔮 Result: {res}")


@cli.command()
@click.argument("training-csv", type=click.Path(dir_okay=False))
@click.argument("out-dir", type=click.Path(file_okay=False))
@click.option("-C", "--svm-cost", type=int, default=3)
@click.option("-l1", "--L1_c", type=float, default=0.1)
@click.option("-l2", "--L2_c", type=float, default=0.1)
@click.option("-i", "--max-iter", type=int, default=100)
def train_nlu(
    training_csv: str,
    out_dir: str,
    C: int,
    L1_c: float,
    L2_c: float,
    max_iterations: int,
):
    """Trains the intent-classifier and entity-tagger based on the data provided
    in the CSV.

    The CSV should contain the following columns: 'id', 'text', 'entities', 'intent'
    (see: 'nlu/data/fiona-nlu-at-2022-04-27-13-12.csv')

    Args:
        training_csv (str): CSV containing the training data
        outdir (str): Directory where to store the resulting models
        C (int): C (cost) SVM hyper-parameter
        L1_c (float): L1 C (L1 regularization) SVM hyper-parameter
        L2_c (float): L2 C (L2 regularization) SVM hyper-parameter
        max_iterations (int): Max training iterations for SVM
    """
    if not training_csv.exists():
        print(f"💥 training CSV not found at '{training_csv}'")
        exit(1)

    train(training_csv, out_dir, C, L1_c, L2_c, max_iterations)


@cli.command()
@click.option("-p", "--port", type=int, default=8000)
@click.option(
    "-c",
    "--classifier",
    type=click.Path(dir_okay=False),
    default="nlu/models/intent-clf.pkl",
)
@click.option(
    "-l",
    "--label-encoder",
    type=click.Path(dir_okay=False),
    default="nlu/models/intent-le.pkl",
)
@click.option(
    "-t",
    "--entity-tagger",
    type=click.Path(dir_okay=False),
    default="nlu/models/intent-tagger.pkl",
)
def start_server(port, classifier, label_encoder, entity_tagger):
    # Create the handler
    nlp = NLUPipeline(classifier, label_encoder, entity_tagger)
    init_handler_and_run_server(nlp, port)


if __name__ == "__main__":
    cli()
