import json
import os
import pickle
import sys
from pathlib import Path

import pandas as pd
import spacy
from sklearn.model_selection import train_test_split

from nlu.modules.entity_extractor import EntityTagger, to_conll_format
from nlu.modules.intent_clf import IntentPredictor


def df_to_conll(df: pd.DataFrame, nlp):
    """Transform into CONLL format.
    The dataframe must have the following keys:
    - text (str): sentence sample
    - entities: (str): json string with the entities list.
                       Each with {text,start,end} keys

    Returns a List of conll sentences.
    Each sentence is a list of tuples; (token, POS-tag, label)
    """
    sents = []
    for _, row in df.iterrows():
        sent, entities = row[["text", "entities"]]
        sents.append(to_conll_format(sent, json.loads(entities), nlp))

    return sents


def train(
    training_csv: Path,
    out_dir: Path,
    C: int = 3,
    L1_c: float = 0.1,
    L2_c: float = 0.1,
    max_iterations: int = 100,
):
    # Hyperparameters: SVC and CRF configuration
    try:
        training_csv = sys.argv[1]
        out_dir = sys.argv[2]
    except IndexError:
        print(
            "❌ Missing parameters!\n"
            "Run e.g.: python -m nlu.train "
            "./nlu/data/fiona-nlu-at-2022-04-27-13-12.csv ./nlu/models"
        )
        sys.exit(1)

    # Read csv data and split into train / test
    df = pd.read_csv(training_csv)
    df = df[~df.isna().any(axis=1)][["id", "text", "entities", "intent"]]
    df_train, df_test = train_test_split(df, test_size=0.3, stratify=df["intent"])

    # labels = df.intent.unique()
    # NOTE: not using ''x_test' or 'y_test' for now
    x_train, _ = df_train["text"], df_test["text"]
    y_train, _ = df_train["intent"], df_test["intent"]

    # Load the just downloaded model
    nlp = spacy.load("en_core_web_sm")

    # Init the Intent classifier
    intd = IntentPredictor(nlp=nlp, C=C)
    intd.train(x_train, y_train)

    # Transform to CoNLL 2002 format
    train_conll = df_to_conll(df_train, nlp)
    # test_conll = df_to_conll(df_test, nlp)

    # Train the CRF tagger
    entity_tagger = EntityTagger(
        c1=L1_c, c2=L2_c, max_iterations=max_iterations, nlp=nlp
    )
    entity_tagger.fit(train_conll)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exists_ok=True)

    print("💾 Saving Intent Detector to disk")
    with open(os.path.join(out_dir, "intent-clf.pkl"), "wb") as f:
        pickle.dump(intd.clf, f)
    with open(os.path.join(out_dir, "intent-le.pkl"), "wb") as f:
        pickle.dump(intd.le, f)

    print("💾 Saving Entity Tagger to disk")
    with open(os.path.join(out_dir, "entity-tagger.pkl"), "wb") as f:
        pickle.dump(entity_tagger.tagger, f)
