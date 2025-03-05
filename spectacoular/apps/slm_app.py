import sys
import subprocess
import spectacoular
from pathlib import Path

def main():
    app_dir = Path(spectacoular.__file__).parent.parent / "apps"  
    command = ["bokeh", "serve", app_dir/"SLM" ]
    command.extend(sys.argv[1:])  # Capture additional arguments like --port 5007)
    # Run the command
    subprocess.run(command)