# ------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
# ------------------------------------------------------------------------------
"""Basic plotting with Bokeh.

.. _basic_mic_geom_plot:

This example creates a simple plot of a microphone array geometry loaded
from an XML file using Acoular and Bokeh.

.. bokeh-plot:: ../examples/basic_mic_geom_plot.py
   :source-position: none

.. note::
    This example creates a standalone Bokeh document and can be run directly with Python.
    It does not require a Bokeh server.

"""

# %%
# First, we import the necessary modules.

from pathlib import Path

import acoular as ac

from bokeh.io import show
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure

# %%
# Next, we set up the microphone geometry with Acoular's
# :class:`~acoular.microphones.MicGeom` class.
# For demonstration purposes, we use a 64 channel Vogel's spiral microphone
# array geometry stored in an XML file that is part of the Acoular package.
# To locate the
# `XML directory <https://github.com/acoular/acoular/tree/master/acoular/xml>`_
# in the Acoular package, we use the :class:`~pathlib.Path` object to
# dynamically construct the path relative to the Acoular package location.

mics = ac.MicGeom(file=Path(ac.__file__).parent / 'xml' / 'tub_vogel64.xml')

# %%
# The :class:`~acoular.microphones.MicGeom` class stores the microphone positions in an attribute
# called :attr:`~acoular.microphones.MicGeom.pos_total`, which is a NumPy array containing the 3D
# coordinates of each microphone in the array.

# %%
# Now, let's create a Bokeh :class:`~bokeh.plotting.figure` to visualize the microphone positions.

figure = figure(
    title='Microphone Geometry',
    tools='hover,zoom_in,zoom_out,reset,lasso_select',
    sizing_mode='stretch_width',
    match_aspect=True,
)


# %%
# A convenient way to provide data to a Bokeh
# :class:`~bokeh.plotting.Plot` is to use a
# :class:`~bokeh.models.ColumnDataSource`, which allows us to update the
# data in the plot easily. Since we create a 2D plot, we only need the *x*
# and *y* coordinates of the microphones.

source = ColumnDataSource(data={'x': mics.pos_total[0], 'y': mics.pos_total[1]})

# %%
# In addition, we need to decide which
# `glyph <https://docs.bokeh.org/en/latest/docs/reference/models/glyphs.html#module-bokeh.models.glyphs>`_
# to use. Glyphs are the basic building blocks of Bokeh plots and define
# how the data is visualized. In this case, we use the
# :meth:`~bokeh.plotting.figure.circle` method to create a
# :class:`~bokeh.models.glyphs.Circle` that represents the microphones.
figure.circle(
    x='x',
    y='y',
    radius=0.02,
    line_color='black',
    fill_color='#1F77B4',
    fill_alpha=0.4,
    source=source,
)


# %%
# Finally, we can show the plot using Bokeh's :func:`~bokeh.io.show` function. This will open a new
# browser window and display the plot with the microphone positions.
#
show(figure)  # Show the plot in a new browser window (standalone HTML)
