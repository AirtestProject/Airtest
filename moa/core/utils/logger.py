import logging


logging.basicConfig(
    level=logging.DEBUG, 
    format='[%(asctime)s][%(levelname)s]<%(name)s> %(message)s', 
    datefmt='%I:%M:%S'
)


def get_logger(name):
    return logging.getLogger(name)
