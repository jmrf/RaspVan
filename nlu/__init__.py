import logging
import os
from typing import Any, Dict, List, Union

import spacy

from common.utils.io import init_logger
from nlu.entity_extractor import EntityTagger
from nlu.intent_clf import IntentPredictor

logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


class NLUPipeline:
    def __init__(
        self,
        clf_pkl: str,
        le_pkl: str,
        tagger_pkl: str,
        nlp_model_name: str = "en_core_web_sm",
    ) -> None:
        # Load a unique spacy model shared by both components so we take up less memory
        nlp = spacy.load(nlp_model_name)
        self.ip = IntentPredictor.from_pretrained(clf_pkl, le_pkl, nlp)
        self.et = EntityTagger.from_pretrained(tagger_pkl, nlp)

    def __call__(self, sentences: Union[list[str], str]) -> list[dict[str, Any]]:
        if isinstance(sentences, str):
            sentences = [sentences]

        intents = self.ip.predict(sentences)
        entities = [
            [
                {"entity": tok[1].split("-")[1], "value": tok[0]}
                for tok in ent
                if tok[1] != "O"
            ]
            for ent in self.et.predict(sentences)
        ]

        return [
            {"sentence": sent, "intent": intent, "entities": ents}
            for sent, intent, ents in zip(sentences, intents, entities)
        ]


if __name__ == "__main__":
    import sys

    nlp = NLUPipeline(
        "nlu/models/intent-clf.pkl",
        "nlu/models/intent-le.pkl",
        "nlu/models/entity-tagger.pkl",
    )

    for line in sys.stdin:
        res = nlp([line.strip()])[0]
        print(res)
