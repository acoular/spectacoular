"""Bokeh CLI entry point for the measurement app."""

from spectacoular.apps.measurement_app.main import server_doc

from bokeh.io import curdoc

server_doc(curdoc())
