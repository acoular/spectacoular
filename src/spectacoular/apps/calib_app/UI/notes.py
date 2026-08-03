"""Text input widget for calibration notes."""

from .tooltips import info_label

from bokeh.layouts import column
from bokeh.models import TextAreaInput


class NotesInput:
    """Free-text input for calibration session notes.

    Attributes
    ----------
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
