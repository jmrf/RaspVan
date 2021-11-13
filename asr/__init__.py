import logging

from deepspeech import Model

from common.utils.io import init_logger
from common.utils.decorators import timeit

logger = logging.getLogger(__name__)
init_logger(level=logging.DEBUG, logger=logger)


@timeit
def load_model(model, scorer):
    """Load the pre-trained model into the memory

    Args:
        models ([type]): Output Grapgh Protocol Buffer file
        scorer ([type]): Scorer file

    Returns:
        [DeepSpeech Object]: A DeepSpeech Model
    """

    ds = Model(model)
    ds.enableExternalScorer(scorer)

    return ds
