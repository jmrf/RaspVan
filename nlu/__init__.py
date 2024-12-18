import logging
import os
from typing import Any, Dict, List, Union

import spacy

from common.utils.io import init_logger
from nlu.modules.entity_extractor import EntityTagger
from nlu.modules.intent_clf import IntentPredictor

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
        logger.info("📥 Loading Spacy '{nlp_model_name}'")
        nlp = spacy.load(nlp_model_name)
        logger.info("📥 Loading Intent-Predictor, label-encoder and Entity-Tagger")
        self.ip = IntentPredictor.from_pretrained(clf_pkl, le_pkl, nlp)
        self.et = EntityTagger.from_pretrained(tagger_pkl, nlp)
        logger.info("✅ Done")

    def __call__(self, sentences: Union[List[str], str]) -> List[Dict[str, Any]]:
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
