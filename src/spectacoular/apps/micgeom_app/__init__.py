"""Mic geometry app package."""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the mic geometry Bokeh app."""
    command = ['bokeh', 'serve', Path(__file__).parent]
    command.extend(sys.argv[1:])
    subprocess.run(command, check=False)  # noqa: S603
