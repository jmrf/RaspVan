import json
import os
import pickle
from pathlib import Path

import pandas as pd
import spacy
from sklearn.model_selection import train_test_split

from nlu.modules.entity_extractor import EntityTagger
from nlu.modules.intent_clf import IntentPredictor


def train(
    training_csv: Path,
    out_dir: Path,
    C: int = 3,
    L1_c: float = 0.1,
    L2_c: float = 0.1,
    max_iterations: int = 100,
):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exists_ok=True)

    # Read csv data and split into train / test
    df = pd.read_csv(training_csv)
    df = df[~df.isna().any(axis=1)][["id", "text", "entities", "intent"]]
    df_train, df_test = train_test_split(df, test_size=0.3, stratify=df["intent"])

    # Load the just downloaded model
    nlp = spacy.load("en_core_web_sm")

    # Init, train and eval the Intent-Classifier
    print("🏋️ Fitting Intent predictor...")
    intd = IntentPredictor(nlp=nlp, C=C)
    intd.fit(df_train["text"], df_train["intent"])

    print("📊 Evaluating Intent predictor...")
    intd.eval(df_test["text"], df_test["intent"])

    print("💾 Saving Intent Detector and label-encoder to disk")
    with open(os.path.join(out_dir, "intent-clf.pkl"), "wb") as f:
        pickle.dump(intd.clf, f)
    with open(os.path.join(out_dir, "intent-le.pkl"), "wb") as f:
        pickle.dump(intd.le, f)

    # Init, train and eval the CRF tagger
    print("🏋️ Fitting Entity Tagger...")
    entity_tagger = EntityTagger(
        c1=L1_c, c2=L2_c, max_iterations=max_iterations, nlp=nlp
    )
    entity_tagger.fit(df_train["text"], [json.loads(e) for e in df_train["entities"]])
    entity_tagger.eval(df_test["text"], [json.loads(e) for e in df_test["entities"]])

    print("💾 Saving Entity Tagger to disk")
    with open(os.path.join(out_dir, "entity-tagger.pkl"), "wb") as f:
        pickle.dump(entity_tagger.tagger, f)
