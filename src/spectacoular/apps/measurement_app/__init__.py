"""Measurement app package."""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the measurement Bokeh app via the Bokeh CLI."""
    command = ['bokeh', 'serve', Path(__file__).with_name('measurement_app.py')]
    command.extend(sys.argv[1:])
    subprocess.run(command, check=False)  # noqa: S603
