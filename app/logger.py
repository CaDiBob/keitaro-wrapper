import logging

from app.config import settings


logger = logging.getLogger("keitaro_wrapper")

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
)

logger.addHandler(handler)
logger.setLevel(settings.LOG_LEVEL)
logger.propagate = False
