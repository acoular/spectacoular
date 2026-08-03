"""Calibration Application entry point.

Run with: uv run calib_app
"""
from pathlib import Path

from .help.help_doc import help_doc
from .main import server_doc

from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.server.server import Server
from tornado.web import StaticFileHandler


def main():
    """Start the Bokeh server for the calibration application.

    Creates a Bokeh server with:
    - Main application at /
    - Help page at /help
    - Static file handler for help page assets
    - 1-hour session token expiration
    """
    server = Server(
        {
            "/": Application(FunctionHandler(server_doc)),
            "/help": Application(FunctionHandler(help_doc))
        },
        # Static handler for serving images/css to the help page
        extra_patterns=[
            (r"/help_static/(.*)", StaticFileHandler, {'path': str(Path(__file__).parent / "help_static")})
        ],
        session_token_expiration=3600,  # 1 hour
    )
    server.start()
    print("Opening Calibration App on http://localhost:5006/")
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
