Custom applications
===================

SpectAcoular applications should subclass
:class:`~spectacoular.apps.base.BaseApp`. The base class owns the shared Bokeh
page template, header, exit button, and light/dark theme switch. A custom app
only needs to provide its page content by implementing ``build_root()``.

.. code-block:: python

    from bokeh.document import Document
    from bokeh.layouts import column
    from bokeh.models import Div
    from spectacoular.apps.base import BaseApp
    from spectacoular.themes import get_acoular_color


    class MyApp(BaseApp):
        title = "My SpectAcoular app"
        default_theme = "light"  # use "dark" for the dark theme

        def build_root(self):
            brand = get_acoular_color("brand")
            return column(
                Div(text=f'<b style="color: {brand};">Hello SpectAcoular</b>'),
                sizing_mode="stretch_width",
            )


    def server_doc(doc: Document):
        MyApp(doc).server_doc()

Run the app with Bokeh, for example:

.. code-block:: bash

    bokeh serve --show my_app.py

Use the strings ``"dark"`` and ``"light"`` to select the initial theme via
``default_theme``. The public helpers in :mod:`spectacoular.themes` are limited
to ``get_theme()`` and ``get_acoular_color()``; subclasses normally only need
``get_acoular_color()`` for app-specific glyphs or inline styles. ``BaseApp``
uses ``get_theme()`` internally to install the document template and configure
the fast client-side theme switch.
