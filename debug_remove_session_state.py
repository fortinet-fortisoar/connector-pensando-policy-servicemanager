from .utils import _debug_remove_session_state
import requests
from connectors.core.connector import get_logger, ConnectorError
from .constants import LOGGER_NAME
logger = get_logger(LOGGER_NAME)


def debug_remove_session_state(*args):
    _debug_remove_session_state()
