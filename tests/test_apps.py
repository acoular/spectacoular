import sys
from pathlib import Path
import spectacoular
import pytest
import importlib
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler

sys.path.append(str(Path(spectacoular.__file__).parent.parent / "apps"  ))  # Add the parent directory to sys.path

@pytest.fixture
def bokeh_server(request):
    # Dynamically import the server_doc based on the app name
    app_name = request.param  # Parameterized fixture
    try:
        app_module = importlib.import_module(f"{app_name}.main")
        server_doc = getattr(app_module, "server_doc")
    except (ModuleNotFoundError, AttributeError) as e:
        pytest.fail(f"Failed to import server_doc from {app_name}.main: {e}")

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
                if "Address already in use" in str(e):
                    print(f"Port {port} is in use. Trying next port...")
                else:
                    pytest.fail(f"Error starting the server: {e}")
        if server is None:
            pytest.fail(f"Failed to start the server. No available ports in range {default_port}-{max_port}.")
    finally:
        if server:
            server.stop()

# indirect: passs the parameter to the fixture before the test
@pytest.mark.parametrize("bokeh_server", [
    "SLM", "FreqBeamformingExample", "MicGeomExample", "RotatingExample", "TimeSamplesExample"], indirect=True) 
def test_bokeh_app(bokeh_server):
    bokeh_server.start()
    assert bokeh_server.io_loop is not None, "Bokeh server failed to start."