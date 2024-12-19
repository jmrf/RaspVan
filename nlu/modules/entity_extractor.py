import itertools
import logging
import os
import pickle
from typing import Any, Dict, List, Optional, Tuple

import sklearn_crfsuite
import spacy
from sklearn.metrics import classification_report

from common.utils.io import init_logger

logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


conll_sent = List[Tuple[str, str, str]]


class EntityTagger:
    default_config = {
        "spacy_pos_model": "en_core_web_sm",
        "L1_c": 0.1,  # coefficient for L1 penalty
        "L2_c": 0.1,  # coefficient for L2 penalty
        "max_iterations": 50,  # early stopping,
        "all_transitions": True,  # include possible but not observed transitions
    }

    def __init__(
        self,
        c1: Optional[float] = None,
        c2: Optional[float] = None,
        max_iterations: Optional[int] = None,
        all_transitions: bool = True,
        verbose: bool = False,
        nlp: Optional[spacy.language.Language] = None,
    ):
        if nlp is not None:
            self.nlp_pos = nlp
        else:
            logger.info("Loading Spacy POS model")
            self.nlp_pos = nlp or spacy.load(self.default_config["spacy_pos_model"])

        self.tagger = sklearn_crfsuite.CRF(
            algorithm="lbfgs",
            c1=c1 or self.default_config["L1_c"],
            c2=c2 or self.default_config["L2_c"],
            max_iterations=max_iterations or self.default_config["max_iterations"],
            all_possible_transitions=all_transitions
            or self.default_config["all_transittions"],
            verbose=verbose,
        )

    @classmethod
    def from_pretrained(
        cls, tagger_pkl: str, nlp: Optional[spacy.language.Language] = None
    ):
        et = cls(nlp=nlp)

        logger.info("Loading tagger CRF model")
        with open(tagger_pkl, "rb") as f:
            et.tagger = pickle.load(f)

        return et

    def fit(self, sentences: List[str], entities: List[List[Dict[str, Any]]]) -> None:
        x, y = self._encode(sentences, entities)
        self.tagger.fit(x, y)

    def predict(self, sentences: List[str]) -> List[List[Tuple[str, str]]]:
        sentence_tokens = self._pos_tokenize(sentences)
        x = [self._sent2features(s) for s in sentence_tokens]
        y = self.tagger.predict(x)
        preds = []
        for sent, pred in zip(x, y):
            words = [s["word.lower()"] for s in sent]
            preds.append(list(zip(words, pred)))

        return preds

    def eval(self, sentences: List[str], entities: List[List[Dict[str, Any]]]) -> None:
        def flatten(lol):
            # flatten a list of lists
            return list(itertools.chain(*lol))

        # Encode and predict
        x, y_true = self._encode(sentences, entities)
        y_pred = self.tagger.predict(x)

        # Classification report
        print(classification_report(flatten(y_true), flatten(y_pred)))

    def _pos_tokenize(self, sentences: List[str]):
        """Encode sentences as a list of (token, POS-tag)"""
        return [
            [(str(tok), tok.pos_) for tok in self.nlp_pos(sent)] for sent in sentences
        ]

    def _encode(self, sentences: List[str], entities: List[List[Dict[str, Any]]]):
        """Encode sentences as a list of (token, POS-tag, entity-label)"""
        datapoints = [
            to_conll_format(s, e, self.nlp_pos) for s, e in zip(sentences, entities)
        ]
        x = [self._sent2features(d) for d in datapoints]
        y = [self._sent2labels(d) for d in datapoints]

        return x, y

    @staticmethod
    def _word2features(pos_tokenized_sentence, i):
        word = pos_tokenized_sentence[i][0]
        postag = pos_tokenized_sentence[i][1]

        features = {
            "bias": 1.0,
            "word.lower()": word.lower(),
            "word[-3:]": word[-3:],
            "word[-2:]": word[-2:],
            "word.isupper()": word.isupper(),
            "word.istitle()": word.istitle(),
            "word.isdigit()": word.isdigit(),
            "postag": postag,
            "postag[:2]": postag[:2],
        }
        if i > 0:
            word1 = pos_tokenized_sentence[i - 1][0]
            postag1 = pos_tokenized_sentence[i - 1][1]
            features.update(
                {
                    "-1:word.lower()": word1.lower(),
                    "-1:word.istitle()": word1.istitle(),
                    "-1:word.isupper()": word1.isupper(),
                    "-1:postag": postag1,
                    "-1:postag[:2]": postag1[:2],
                }
            )
        else:
            features["BOS"] = True

        if i < len(pos_tokenized_sentence) - 1:
            word1 = pos_tokenized_sentence[i + 1][0]
            postag1 = pos_tokenized_sentence[i + 1][1]
            features.update(
                {
                    "+1:word.lower()": word1.lower(),
                    "+1:word.istitle()": word1.istitle(),
                    "+1:word.isupper()": word1.isupper(),
                    "+1:postag": postag1,
                    "+1:postag[:2]": postag1[:2],
                }
            )
        else:
            features["EOS"] = True

        return features

    @staticmethod
    def _sent2labels(sent: conll_sent):
        return [label for _, _, label in sent]

    @staticmethod
    def _sent2tokens(sent: conll_sent):
        return [token for token, _, _ in sent]

    @staticmethod
    def _sent2features(sent: conll_sent):
        return [EntityTagger._word2features(sent, i) for i in range(len(sent))]


def to_conll_format(
    sent: str, entities: List[Dict[str, str]], nlp
) -> List[Tuple[str, str, str]]:
    """Transform a sentence into CONLL annotation format.

    Args:
        sent (str): sentence to encode
        entities: (List): Entity list. Each with {text,start,end} keys
        nlp (Spacy.nlp): Spacy POS tagger

    Returns a sentence as a list of tuples; (token, POS-tag, label)
    """
    # Gather the entities in the sentence
    entity_map = {}
    for ent in entities:
        ent_value = ent["text"]
        ent_lbl = ent["labels"][0]
        entity_map[ent_value] = ent_lbl

    # For each token tag it with its entity label (as Inside: I-{lbl})
    encoded = []
    for tok in nlp(sent):
        token = str(tok)
        lbl = entity_map.get(token)
        lbl = f"I-{lbl}" if lbl else "O"
        encoded.append((token, tok.pos_, lbl))

    return encoded
