from .utils import _debug_expire_cookie
from connectors.core.connector import get_logger
from .constants import LOGGER_NAME


logger = get_logger(LOGGER_NAME)


def debug_expire_cookie(config, params):
    _debug_expire_cookie(config)
