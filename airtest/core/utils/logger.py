import logging
import sys


logging.basicConfig(
    # level=logging.DEBUG,  # do not set level in global, to avoid other modules output
    format='[%(asctime)s][%(levelname)s]<%(name)s> %(message)s', 
    datefmt='%I:%M:%S',
    stream=sys.stdout
)


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    return logger
