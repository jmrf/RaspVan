from typing import Any
from typing import Dict
from typing import List
from typing import Union

import spacy

from nlu.entity_extractor import EntityTagger
from nlu.intent_clf import IntentPredictor


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

    def __call__(self, sentences: Union[List[str], str]) -> List[Dict[str, Any]]:
        self.run(sentences)

    def run(self, sentences: Union[List[str], str]) -> List[Dict[str, Any]]:
        if isinstance(sentences, str):
            sentences = [sentences]

        intents = self.ip.predict(sentences)
        entities = [
            {"entity": tok[1].split("-")[1], "value": tok[0]}
            for ent in self.et.predict(sentences)
            for tok in ent
            if tok[1] != "O"
        ]

        return [
            {"sentence": sent, "intent": intent, "entities": ents}
            for sent, intent, ents in zip(sentences, intents, entities)
        ]


if __name__ == "__main__":
    nlp = NLUPipeline(
        "nlu/models/intent-clf.pkl",
        "nlu/models/intent-le.pkl",
        "nlu/models/entity-tagger.pkl",
    )

    res = nlp(["switch off the back light", "turn on all the lights!"])

    print(res)
