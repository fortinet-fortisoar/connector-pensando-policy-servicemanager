"""debug expire cookie"""

from connectors.core.connector import get_logger
from .constants import LOGGER_NAME
from .utils import _debug_expire_cookie


logger = get_logger(LOGGER_NAME)


def debug_expire_cookie(config, params):
    _debug_expire_cookie(config)
