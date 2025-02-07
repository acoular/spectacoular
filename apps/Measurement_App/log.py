import logging
from bokeh.models.widgets import TextAreaInput
from layout import COLOR
from collections import deque

class LogWidget:
    """A class providing a Bokeh TextAreaInput widget for logging and simultaneously writing logs to a file."""

    def __init__(self, logname="MeasurementApp.log", loglength=50, loglevel=logging.DEBUG, background=COLOR[1]):
        self.loglength = loglength

        # Create Bokeh TextAreaInput widget for log display
        self.log_text = TextAreaInput(title="App Log", value="", width=500, height=800, disabled=True, background=background)

        # Create logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(loglevel)

        # Create file handler for logging to a file
        file_handler = logging.FileHandler(logname, mode="w")
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))

        # Create custom handler that updates the Bokeh widget
        widget_handler = LogWidgetHandler(self.log_text, loglength)
        widget_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(widget_handler)

        # Ensure root logger does not propagate logs to default handlers (to avoid duplication)
        self.logger.propagate = False

        self.logger.info("Measurement App started...")

class LogWidgetHandler(logging.Handler):
    """ Custom logging handler that updates a Bokeh TextAreaInput widget. """
    def __init__(self, log_text_widget, loglength):
        super().__init__()
        self.log_text_widget = log_text_widget
        self.log_messages = deque(maxlen=loglength)  # Efficient fixed-length queue

    def emit(self, record):
        """ Write log message to the widget and keep a history of loglength lines. """
        self.log_messages.append(self.format(record))
        self.log_text_widget.value = "\n".join(self.log_messages)

