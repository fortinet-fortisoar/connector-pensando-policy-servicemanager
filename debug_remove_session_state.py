from .utils import _debug_remove_session_state
from connectors.core.connector import get_logger
from .constants import LOGGER_NAME


logger = get_logger(LOGGER_NAME)


def debug_remove_session_state(*args):
    _debug_remove_session_state()
