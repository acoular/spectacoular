"""FFT spectrum visualization for calibration signals."""

import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.layouts import column
from .tooltips import info_label
from ..util import V_to_dBV


class FFTViewer:
    """Live FFT spectrum plot for visualizing calibration channel signals.
    
    Shows relative amplitude vs frequency. The y-axis has fixed tick spacing
    (Y_DELTA dB) but no absolute scale — it's purely relative for visualizing
    signal stability and frequency content.
    
    Attributes:
        fft: FFT generator instance (FFT preprocessor).
        source: ColumnDataSource with frequency/amplitude data.
        plot: Bokeh figure instance.
        title: Info label for the plot.
        delta_label: Label showing the dB spacing.
    """

    # Fixed tick spacing (delta) in dB
    Y_DELTA = 10

    def __init__(self, fft_generator):
        """Initialize the FFT viewer.
        
        Args:
            fft_generator: FFT preprocessor instance providing spectrum data.
        """
        self.fft = fft_generator

        self.source = ColumnDataSource(
            data={"frequency": [], "amplitude": []}
        )

        self.plot = figure(
            height=583,
            sizing_mode="stretch_width",
            x_axis_label="Frequency (Hz)",
            y_axis_label=f"Amplitude  (dBV)",
            x_range=(-100, 8000),
            y_range=(-150, 0),
            background_fill_color="#fafafa",
            border_fill_color="white",
        )

      
        self.title = info_label(
            "FFT Spectrum",
            "Live-Spectrum of the active Channel.",
            direction="down"
        )

       
    
        self.plot.xgrid.grid_line_color = "#e0e0e0"
        self.plot.ygrid.grid_line_color = "#e0e0e0"
        self.plot.ygrid.grid_line_dash = "dashed"
        self.plot.xgrid.grid_line_dash = "dashed"
        self.plot.outline_line_color = None
        self.plot.xaxis.axis_label_text_font_style = "bold"
        self.plot.yaxis.axis_label_text_font_style = "bold"


        # ---- Line ----
        self.plot.line(
            x="frequency", y="amplitude", source=self.source,
            line_width=2, line_color="#1f77b4",
        )
        self._widget = None

    def update(self, num):
        """Update plot data from FFT generator for the selected channel.
        
        Args:
            num: Channel identifier string (e.g., "Channel 1").
        """
        try:
            result = next(self.fft.result())
            spectrum = result[int(num.split()[1]) - 1, :]
            amplitude = V_to_dBV(np.abs(spectrum))
            frequency = self.fft.frequencies

            self.source.data = {
                "frequency": frequency,
                "amplitude": amplitude,
            }
        except Exception:
            self.source.data = {"frequency": [], "amplitude": []}

    def widget(self):
        """Get the plot widget layout (cached after first call).
        
        Returns:
            column: Bokeh column layout containing title and plot.
        """
        # Always return the same layout
        if self._widget is None:
            self._widget = column(
                self.title,
                self.plot,
                sizing_mode="stretch_width",
            )
        return self._widget