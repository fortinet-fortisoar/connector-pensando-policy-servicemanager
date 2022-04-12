"""debug remove session state"""

from connectors.core.connector import get_logger
from .constants import LOGGER_NAME
from .utils import PensandoPSM


logger = get_logger(LOGGER_NAME)


def debug_remove_session_state(config, params):
    psm = PensandoPSM(config)
    psm._debug_remove_session_state()
