import sys
import subprocess
from pathlib import Path


def main():
    app_dir = Path(__file__).parent
    command = ["bokeh", "serve", app_dir / "FreqBeamformingExample"]
    command.extend(sys.argv[1:])  # Capture additional arguments like --port 5007)
    # Run the command
    subprocess.run(command)
