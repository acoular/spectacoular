

def main():
    from bokeh.server.server import Server
    from bokeh.application import Application
    from bokeh.application.handlers.function import FunctionHandler
    from .main import server_doc

    server = Server({"/" : Application(FunctionHandler(server_doc))})
    server.start()
    print("Opening Measurement App on http://localhost:5006/")
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
