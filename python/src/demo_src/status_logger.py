import logging
import logging.handlers

logger = logging.getLogger("Status bar logger")


class StatusBarLogHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        self._write_function = None

    def emit(self, record):
        if self._write_function is None:
            return
        # some formatting if needed here
        msg = self.format(record)
        self._write_function(msg)

    def set_write_function(self, write_function):
        self._write_function = write_function

    def setup_for_logging(self):
        status_bar_formatter = logging.Formatter("%(message)s")
        self.setFormatter(status_bar_formatter)
        logger = logging.getLogger("Status bar logger")
        logger.addHandler(self)
        logger.setLevel(logging.DEBUG)









