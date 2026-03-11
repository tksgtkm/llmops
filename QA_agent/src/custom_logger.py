import logging
import sys

def setup_logger(name, level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)

    return logger