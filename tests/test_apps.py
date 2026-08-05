"""Tests for SpectAcoular Bokeh application entry points."""

import importlib
import os

import pytest
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.server.server import Server


@pytest.fixture
def bokeh_server(request):
    """Create a Bokeh server for the requested application module."""
    # Dynamically import the server_doc based on the app name
    app_name = request.param  # Parameterized fixture
    try:
        app_module = importlib.import_module(f'spectacoular.apps.{app_name}.main')
        server_doc = app_module.server_doc
    except (ModuleNotFoundError, AttributeError) as e:
        pytest.fail(f'Failed to import server_doc from {app_name}.main: {e}')

    # Create a Bokeh application
    bokeh_app = Application(FunctionHandler(server_doc))
    default_port = 5006
    max_port = 5010
    server = None

    try:
        for port in range(default_port, max_port + 1):
            try:
                server = Server({'/': bokeh_app}, port=port)
                yield server  # Provide the server to the test
                break
            except OSError as e:
                if 'Address already in use' not in str(e):
                    pytest.fail(f'Error starting the server: {e}')
        if server is None:
            pytest.fail(f'Failed to start the server. No available ports in range {default_port}-{max_port}.')
    finally:
        if server:
            server.stop()


# Skip the test for the "SLM" app if the operating system is Windows
@pytest.mark.parametrize(
    'bokeh_server',
    [
        pytest.param(
            'level_meter_app',
            marks=pytest.mark.skipif(os.name == 'nt', reason='Test is not supported on Windows.'),
        ),
        'micgeom_app',
        'bf_example_app',
        'rotating_example_app',
        'data_viewer_app',
    ],
    indirect=True,
)
def test_bokeh_app(bokeh_server):
    """Test that each configured Bokeh application server starts."""
    bokeh_server.start()
    if bokeh_server.io_loop is None:
        pytest.fail('Bokeh server failed to start.')
