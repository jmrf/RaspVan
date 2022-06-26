import logging
import os
from typing import List
from typing import Optional

import numpy as np
import spacy
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

from common.utils.io import init_logger


logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


class IntentDetector:
    def __init__(self, C: int = 3) -> None:
        # Load the spacy model: nlp
        self.nlp_vec = spacy.load("en_core_web_sm")
        # Calculate the dimensionality of nlp
        self.embedding_dim = self.nlp_vec.vocab.vectors_length
        logger.debug(f"Embedding dimension: {self.embedding_dim}")
        # Instantiate labelencoder object
        self.le = LabelEncoder()
        # Instantiate SVM classifier
        self.clf = SVC(C=C, probability=True)

    def _encode(
        self, sentences: List[str], labels: Optional[List[str]] = None
    ) -> List[np.ndarray]:
        x_vecs = [self.nlp_vec(sent).vector for sent in sentences]
        if labels:
            return x_vecs, self.le.transform(labels)

        return x_vecs

    def train(self, sentences: List[str], labels: List[str]):
        logger.info(f"Training on {len(sentences)} intent examples...")
        # Train the label encoder
        self.le.fit(labels)
        # Sentence & Label encoding
        x_vecs, y_indices = self._encode(sentences, labels)
        # Train the SVM classifier
        self.clf.fit(x_vecs, y_indices)

    def predict(self, sentences: List[str]):
        x_vecs = self._encode(sentences)
        intent_preds = self.clf.predict(x_vecs)
        intent_probs = self.clf.predict_proba(x_vecs)

        return zip(intent_preds, intent_probs)
