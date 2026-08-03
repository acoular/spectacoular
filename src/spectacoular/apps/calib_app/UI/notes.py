"""Text input widget for calibration notes."""

from bokeh.models import TextAreaInput
from bokeh.layouts import column
from .tooltips import info_label


class NotesInput:
    """Free-text input for calibration session notes.
    
    Attributes:
        textarea: TextAreaInput widget for note entry.
        layout: Column layout containing label and text area.
    """
    def __init__(self):
        """Initialize the notes input widget."""
        self.textarea = TextAreaInput(
            value="",
            rows=100,
            placeholder="Add notes ...",
            sizing_mode="stretch_both"
        )
        self.layout = column(
            info_label("Notes", "Free text notes for this calibration which are stored in the .json"),
            self.textarea,
            sizing_mode="stretch_both"
        )
