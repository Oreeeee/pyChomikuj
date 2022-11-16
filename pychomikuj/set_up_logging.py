import logging


def set_up_logging(logging_level):
    logging_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    logging.basicConfig(
        level=logging_levels[logging_level],
        format="%(asctime)s %(levelname)s %(filename)s %(message)s",
    )
