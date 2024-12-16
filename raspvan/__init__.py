import logging
import os

from common.utils.io import init_logger

logger = logging.getLogger(__name__)
init_logger(
    level=os.getenv("LOGGING_LEVEL", logging.INFO),
    logger=logger,
)
