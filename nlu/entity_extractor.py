import logging
import os
from typing import Dict
from typing import List
from typing import Tuple

import sklearn_crfsuite

from common.utils.io import init_logger


logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


conll_sent = List[Tuple[str, str, str]]


class Tagger:

    default_config = {
        "L1_c": 0.1,  # coefficient for L1 penalty
        "L2_c": 0.1,  # coefficient for L2 penalty
        "max_iterations": 50,  # early stopping,
        "all_transitions": True,  # include possible but not observed transitions
    }

    def __init__(
        self,
        c1: float = None,
        c2: float = None,
        max_iterations: int = None,
        all_transitions: bool = True,
        verbose: bool = False,
    ):
        self.tagger = sklearn_crfsuite.CRF(
            algorithm="lbfgs",
            c1=c1 or self.default_config["L1_c"],
            c2=c2 or self.default_config["L2_c"],
            max_iterations=max_iterations or self.default_config["max_iterations"],
            all_possible_transitions=all_transitions
            or self.default_config["all_transittions"],
            verbose=verbose,
        )

    def fit(self, sents: List[conll_sent]):
        x = [self._sent2features(s) for s in sents]
        y = [self._sent2labels(s) for s in sents]
        self.tagger.fit(x, y)

    def predict(self, sents: List[conll_sent]) -> List[List[Tuple[str, str]]]:
        x = [self._sent2features(s) for s in sents]
        y = self.tagger.predict(x)
        preds = []
        for sent, pred in zip(x, y):
            words = [s["word.lower()"] for s in sent]
            preds.append(list(zip(words, pred)))

        return preds

    @staticmethod
    def _word2features(sent, i):
        word = sent[i][0]
        postag = sent[i][1]

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
            word1 = sent[i - 1][0]
            postag1 = sent[i - 1][1]
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

        if i < len(sent) - 1:
            word1 = sent[i + 1][0]
            postag1 = sent[i + 1][1]
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

    def _sent2features(self, sent: conll_sent):
        return [self._word2features(sent, i) for i in range(len(sent))]


def to_conll_format(sent: str, entities: List[Dict[str, str]], nlp):
    """Transform a sentence into CONLL annotation format.
     - sent (str): sentence to encode
     - entities: (list): Entity list. Each with {text,start,end} keys

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
