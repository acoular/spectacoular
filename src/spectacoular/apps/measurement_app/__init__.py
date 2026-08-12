"""Measurement app package."""


def server_doc(doc):
    """Populate a Bokeh document for the measurement app."""
    from .main import server_doc as build_document

    build_document(doc)


def main():
    """Launch the measurement Bokeh app."""
    from bokeh.application import Application
    from bokeh.application.handlers.function import FunctionHandler
    from bokeh.server.server import Server

    server = Server({'/': Application(FunctionHandler(server_doc))})
    server.start()
    print('Opening Measurement App on http://localhost:5006/')
    server.io_loop.add_callback(server.show, '/')
    server.io_loop.start()
