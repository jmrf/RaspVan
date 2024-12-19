import sys
from pathlib import Path

import click

from nlu import NLUPipeline
from nlu.server import init_handler_and_run_server
from nlu.training import train


@click.group()
def cli():
    """NLU pipeline (clasifier and tagger) CLI"""


@cli.command("run")
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
    default="nlu/models/entity-tagger.pkl",
)
def run_nlu_pipeline(classifier, label_encoder, entity_tagger):
    """Run the NLU pipeline

    Args:
        classifier (str): Path to the pickled classifier model
        label_encoder (str): Path to the pickled label-encoder model
        entity_tagger (str): Path to the pickled CRF tagger model
    """
    nlp = NLUPipeline(classifier, label_encoder, entity_tagger)
    for line in sys.stdin:
        res = nlp([line.strip()])[0]
        print(f"🔮 Result: {res}")


@cli.command("train")
@click.argument("training-csv", type=click.Path(dir_okay=False))
@click.argument("out-dir", type=click.Path(file_okay=False))
@click.option("-c", "--svm-cost", type=int, default=10)
@click.option("-l1", "--tagger-l1-penalty", type=float, default=0.3)
@click.option("-l2", "--tagger-l2_penalty", type=float, default=0.3)
@click.option("-i", "--max-iterations", type=int, default=100)
def train_nlu_pipeline(
    training_csv: str,
    out_dir: str,
    svm_cost: int,
    tagger_l1_penalty: float,
    tagger_l2_penalty: float,
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
    training_csv = Path(training_csv)
    if not training_csv.exists():
        print(f"💥 training CSV not found at '{training_csv}'")
        exit(1)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train(
        training_csv,
        out_dir,
        svm_cost,
        tagger_l1_penalty,
        tagger_l2_penalty,
        max_iterations,
    )


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
    default="nlu/models/entity-tagger.pkl",
)
def serve(port, classifier, label_encoder, entity_tagger):
    """Starts a simple http server to serve NLU predictions

    Args:
        port (int): HTTP port to listen to
        classifier (str): Path to the pickled classifier model
        label_encoder (str): Path to the pickled label-encoder model
        entity_tagger (str): Path to the pickled CRF tagger model
    """
    # Create the handler
    nlp = NLUPipeline(classifier, label_encoder, entity_tagger)
    init_handler_and_run_server(nlp, port)


if __name__ == "__main__":
    cli()
