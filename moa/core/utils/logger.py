import logging
import sys

logging.basicConfig(
    level=logging.DEBUG, 
    format='[%(asctime)s][%(levelname)s]<%(name)s> %(message)s', 
    datefmt='%I:%M:%S',
    stream=sys.stdout
)


def get_logger(name):
    return logging.getLogger(name)
