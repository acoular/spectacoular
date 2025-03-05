import logging
import importlib
from bokeh.models.widgets import TextAreaInput
from layout import COLOR
from collections import deque


class LogWidget:
    """A class providing a Bokeh TextAreaInput widget for logging and simultaneously writing logs to a file."""

    def __init__(self, doc, logname="MeasurementApp.log", loglength=50, loglevel=logging.DEBUG, background=COLOR[1]):
        self.doc = doc
        self.loglength = loglength

        # Create Bokeh TextAreaInput widget for log display
        self.log_text = TextAreaInput(title="App Log", value="", disabled=True, background=background,
         sizing_mode="stretch_height", width=300)

        spec = importlib.util.find_spec('tapy')
        if spec is None:
            self.logger = logging.getLogger(__name__)
        else:
            from tapy.core.logger import getLogger
            self.logger = getLogger('tapy')
        self.logger.setLevel(loglevel)

        # Create file handler for logging to a file
        file_handler = logging.FileHandler(logname, mode="w")
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))

        # Create custom handler that updates the Bokeh widget
        widget_handler = LogWidgetHandler(self.doc, self.log_text, loglength)
        widget_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(widget_handler)

class LogWidgetHandler(logging.Handler):
    """ Custom logging handler that updates a Bokeh TextAreaInput widget. """
    def __init__(self, doc, log_text_widget, loglength):
        super().__init__()
        self.log_text_widget = log_text_widget
        self.log_messages = deque(maxlen=loglength)  # Efficient fixed-length queue
        doc.add_periodic_callback(self.update_log_text, 1000)  # Update log text every second

    def emit(self, record):
        """ Write log message to the widget and keep a history of loglength lines. """
        self.log_messages.append(self.format(record))

    def update_log_text(self):
        self.log_text_widget.value = "\n".join(self.log_messages)
