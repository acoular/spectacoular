import subprocess
import sys
from pathlib import Path


def main():
    command = ['bokeh', 'serve', Path(__file__).parent]
    command.extend(sys.argv[1:])
    subprocess.run(command)
