import sys
import subprocess
import spectacoular
from pathlib import Path


def main():
    command = ["bokeh", "serve", Path(__file__).parent / "RotatingExample"]
    command.extend(sys.argv[1:])  # Capture additional arguments like --port 5007)
    # Run the command
    subprocess.run(command)
