"""debug remove session state"""

from connectors.core.connector import get_logger
from .constants import LOGGER_NAME
from .utils import _debug_remove_session_state


logger = get_logger(LOGGER_NAME)


def debug_remove_session_state(config, params):
    _debug_remove_session_state(config)
