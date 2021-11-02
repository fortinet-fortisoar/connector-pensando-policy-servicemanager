from .utils import _debug_expire_cookie
import requests
from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME
logger = get_logger(LOGGER_NAME)


def debug_expire_cookie(config, params):
    _debug_expire_cookie(config)
