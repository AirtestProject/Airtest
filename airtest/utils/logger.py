import logging


def init_logging():
    # logger = logging.root
    # use 'airtest' as root logger name to prevent changing other modules' logger
    logger = logging.getLogger("airtest")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt='[%(asctime)s][%(levelname)s]<%(name)s> %(message)s',
        datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


init_logging()


def get_logger(name):
    logger = logging.getLogger(name)
    return logger
