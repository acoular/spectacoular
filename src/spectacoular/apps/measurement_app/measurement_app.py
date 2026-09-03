"""Bokeh CLI entry point for the measurement app."""

from bokeh.io import curdoc

from spectacoular.apps.measurement_app.main import server_doc

server_doc(curdoc())
