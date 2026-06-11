"""Bokeh entry point for the beamforming example application."""

import subprocess
import sys
from pathlib import Path


def main():
    """Start the beamforming example as a Bokeh server application."""
    command = ['bokeh', 'serve', Path(__file__).parent]
    command.extend(sys.argv[1:])
    subprocess.run(command, check=False)  # noqa: S603
