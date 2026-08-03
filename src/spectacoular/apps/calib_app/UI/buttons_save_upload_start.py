"""
Bokeh UI components for calibration control: path input, file loader, and action buttons.

This module provides reusable UI elements for:
- Specifying save paths for calibration results
- Loading calibration data from JSON files
- Starting/stopping calibration and saving results
"""

from .tooltips import info_label

from bokeh.layouts import column, row
from bokeh.models import Button, Div, FileInput, InlineStyleSheet, TextInput


class PathInput:
    """Text input widget for specifying the calibration save path.

    Attributes
    ----------
        widget: TextInput widget configured for path entry.
        layout: Column layout containing the info label and text input.
    """

    def __init__(self, default):
        """Initialize with a default save path.

        Args:
            default: Default path value to display. (is converted to a string with str())
        """
        self.widget = TextInput(
            value=str(default),
            sizing_mode="stretch_width"
        )
        self.layout = column(
            info_label("Save Path", "Target path for saving the calibration results (.json)"),
            self.widget,
            sizing_mode="stretch_width"
        )

class InputFile:
    """File input widget for loading calibration data from JSON files.

    Attributes
    ----------
        widget: FileInput widget restricted to .json files.
        layout: Column layout containing the info label and file input.
    """

    def __init__(self):
        """Initialize the file input widget."""
        self.widget = FileInput(accept=".json", sizing_mode="stretch_width")
        self.layout = column(
            info_label("Load File", "Select a .json file to load a calibration"),
            self.widget,
            sizing_mode="stretch_width"
        )


class ButtonBar:
    """Control bar with Start, Stop, Save buttons and a Help link.

    Attributes
    ----------
        btn_start: Primary button to start calibration.
        btn_stop: Danger button to stop current calibration.
        btn_save: Button to save calibration results.
        layout: Row layout containing all buttons with labels.
        button_style: Shared InlineStyleSheet for consistent button styling.
    """

    def __init__(self, logger=None):
        """Initialize the button bar.

        Args:
            logger: Optional logger instance for button actions.
        """
        self.logger = logger

        # Shared button style
        self.button_style = InlineStyleSheet(css="""
            :host {
                --bokeh-base-font-size: .72rem;
            }
            .bk-btn {
                border-radius: 4px;
                font-size: .72rem;
                font-weight: 600;
            }
        """)

        self.btn_start = Button(label="Start", button_type="primary",
                                sizing_mode="stretch_width",
                                stylesheets=[self.button_style])
        self.btn_stop = Button(label="Stop", button_type="danger",
                               sizing_mode="stretch_width",
                               stylesheets=[self.button_style])
        self.btn_save = Button(label="Save",
                               sizing_mode="stretch_width",
                               stylesheets=[self.button_style])

        self.layout = row(
            column(
                info_label("Start", "Starts the calibration process"),
                self.btn_start,
                sizing_mode="stretch_width"
            ),
            column(
                info_label("Stop", "Stops the current calibration"),
                self.btn_stop,
                sizing_mode="stretch_width"
            ),
            column(
                info_label("Save", "Saves the calibration results in a .json"),
                self.btn_save,
                sizing_mode="stretch_width"
            ),
            column(
                Div(text="""<a href="http://localhost:5006/help" target="_blank">Help</a>""")
            ),

            sizing_mode="stretch_width"
        )

