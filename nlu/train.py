import json
import os
import pickle
import sys

import pandas as pd
import spacy
from sklearn.model_selection import train_test_split

from nlu.entity_extractor import EntityTagger
from nlu.entity_extractor import to_conll_format
from nlu.intent_clf import IntentDetector


def df_to_conll(df: pd.DataFrame, nlp):
    """Transform into CONLL format.
    The dataframe must have the following keys:
    - text (str): sentence sample
    - entities: (str): json string with the entities list. Each with {text,start,end} keys

    Returns a List of conll sentences. Each sentence is a list of tuples; (token, POS-tag, label)
    """
    sents = []
    for i, row in df.iterrows():
        sent, entities = row[["text", "entities"]]
        sents.append(to_conll_format(sent, json.loads(entities), nlp))

    return sents


if __name__ == "__main__":

    # Hyperparameters: SVC and CRF configuration
    C = 3
    L1_c = 0.1  # @param {"type":"slider", "min":0.1, "max":1, "step": 0.1}
    L2_c = 0.1  # @param {"type":"slider", "min":0.1, "max":1, "step": 0.1}
    max_iterations = 100

    try:
        training_csv = sys.argv[1]  # "nlu/samples/fiona-nlu-at-2022-04-27-13-12.csv"
        out_dir = sys.argv[2]
    except IndexError:
        print(
            "❌ Missing parameters!\n"
            "Run e.g.: python -m nlu.train "
            "./nlu/data/fiona-nlu-at-2022-04-27-13-12.csv ./nlu/models"
        )
        exit(1)

    # Read csv data and split into train / test
    df = pd.read_csv(training_csv)
    df = df[~df.isna().any(axis=1)][["id", "text", "entities", "intent"]]
    df_train, df_test = train_test_split(df, test_size=0.3, stratify=df["intent"])

    labels = df.intent.unique()
    x_train, x_test = df_train["text"], df_test["text"]
    y_train, y_test = df_train["intent"], df_test["intent"]

    # Init the Intent classifier
    intd = IntentDetector(C=C)
    intd.train(x_train, y_train)

    # Load the just downloaded model
    nlp = spacy.load("en_core_web_sm")

    # Transform to CoNLL 2002 format
    train_conll = df_to_conll(df_train, nlp)
    test_conll = df_to_conll(df_test, nlp)

    # Train the CRF tagger
    entity_tagger = EntityTagger(c1=L1_c, c2=L2_c, max_iterations=max_iterations)
    entity_tagger.fit(train_conll)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exists_ok=True)

    print(f"💾 Saving Intent Detector to disk")
    with open(os.path.join(out_dir, "intent-detecor.pkl"), "wb") as f:
        pickle.dump(intd, f)

    print(f"💾 Saving Entity Tagger to disk")
    with open(os.path.join(out_dir, "entity-tagger.pkl"), "wb") as f:
        pickle.dump(entity_tagger, f)
