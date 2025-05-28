# ------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
# ------------------------------------------------------------------------------
"""
.. _interactive_apps:

Build interactive applications with SpectAcoular
================================================

In many cases, a standalone HTML document is not sufficient to provide full interactivity, especially
when computations are required on the Python side to update data shown in the Browser document. 
Bokeh provides a way to host applications that can be run in a web browser, allowing for
interactivity and real-time updates. 

.. image:: https://docs.bokeh.org/en/latest/_images/bokeh_serve.svg
    :width: 600px
    :align: center
    :alt: Bokeh Server Application (see: `Bokeh documentation <https://docs.bokeh.org/en/latest/docs/user_guide/server/app.html#ug-server-apps>`_)


In this example, we are going to create an interactive application to visualize the Beamforming 
result for Acoular's 
`three sources example <https://www.acoular.org/auto_examples/introductory_examples/example_basic_beamforming.html#sphx-glr-auto-examples-introductory-examples-example-basic-beamforming-py>`_ .
As seen by the HTML document below, changing the frequency or grid parameters will **not** result
in an update of the plot, since the HTML document is static and does not allow for interaction with 
the Python code. Instead, it is necessary to run a Bokeh server application hosting the Python code 
to which the client can listen for updates of the data.

To start the Bokeh server, one can run the following command in the terminal:

.. code-block:: bash

    bokeh serve --show spectacoular/examples/interactive_apps.py


.. bokeh-plot:: ../examples/interactive_apps.py
   :source-position: none


"""

# %%
# Create three sources example
# -----------------------------
#
# Let's begin by importing Acoular and setting up the simulation pipeline for the three sources example.

import acoular as ac
import spectacoular as sp
from pathlib import Path

mg = ac.MicGeom( file=Path(ac.__file__).parent / 'xml' / 'array_64.xml' )

# create time data source
three_sources = ac.demo.create_three_sources(mg)


#%%
# Next, we will define a rectangular grid (:class:`~acoular.grids.RectGrid`) discretizing the source area. 
# To obtain a source map at 4 kHz (one-third octave) asociated with the defined grid, 
# we will utilize conventional beamforming (:class:`~acoular.fbeamform.BeamformerBase`).

# set up the rectangular grid
rg = ac.RectGrid(x_min=-0.2, x_max=0.2, y_min=-0.2, y_max=0.2, z=-0.3, increment=0.01)

# set up the beamformer
bb = ac.BeamformerBase(
    freq_data=ac.PowerSpectra(source=three_sources, block_size=128, window='Hanning'), 
    steer=ac.SteeringVector(grid=rg, mics=mg)
    )

# calculate the beamforming result as sound pressure level (Lp/dB)
res = ac.L_p(bb.synthetic(f=4000, num=3)).T

#%%
# Create widgets
# ----------------
#
# To enable interactive changes to the beamforming result, we will create some widgets based on the
# existing processing chain, arranged in a grid layout.

from bokeh.layouts import gridplot # noqa: E402

grid_grid = gridplot(
    list(sp.get_widgets(rg).values()), 
    ncols=2, width=150)


#%% 
# Plot the beamforming result
# ---------------------------
#
# To visualize the beamforming result, we will create figure and use Bokeh's
# :class:`~bokeh.models.Image` glyph, which allows us to display 2D source mappings. 
# The :class:`~bokeh.models.Image` glyph requires us to specify the x and y coordinate sof the bottom 
# left grid corner, the width and height of the grid, and the sound pressure to be displayed.

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, LinearColorMapper
from bokeh.palettes import viridis


source_plot = figure(title='Acoular Three Sources', tools='hover,reset,pan,wheel_zoom')

cds = ColumnDataSource(
    data = {'bfdata' : [res], 'x':[rg.x_min], 'y':[rg.y_min], 'dw':[rg.x_max-rg.x_min], 'dh':[rg.y_max-rg.y_min]}
    )

color_mapper = LinearColorMapper(
    palette=viridis(100), low=res.max()-20, high=res.max())


source_plot.image(
    color_mapper=color_mapper,
    image='bfdata', x='x', y='y', dw='dw', dh='dh',alpha=0.9,
    anchor='bottom_left', origin='bottom_left', source=cds)


#%% 
# The Presenter class
# -------------------
#
# SpectAcoular provides so-called Presenter classes to automatically handle updates of the 
# :class:`~bokeh.models.ColumnDataSource` data whenever the desired evaluation parameters change.
# Here, we will use the :class:`~spectacoular.BeamformerPresenter` class. We choose `auto_update=True`, 
# which means that the data in the :class:`~bokeh.models.ColumnDataSource` will be updated automatically
# whenever the internal state of the beamformer changes.

bf_presenter = sp.BeamformerPresenter(
    source = bb, 
    cdsource = cds,
    freq = 4000,
    num = 3,
    auto_update = True,
)

#%% 
# The :class:`~spectacoular.BeamformerPresenter` class provides two traits, `freq` and `num` that
# can be used to control the frequency and the frequency band width of the beamforming result. As 
# with all :class:`~spectacoular.factory.BaseSpectacoular` classes, we could use the 
# :func:`~spectacoular.factory.get_widgets` function to create Bokeh widgets for these traits.
# However, this time, we will take a different approach and assign an existing widget to the `freq`
# trait via the :func:`~spectacoular.factory.set_widgets` function.

from bokeh.models.widgets import Slider # noqa: E402

freq_slider = Slider(title='f/Hz',value=bf_presenter.freq, start=500.0, end=10000.0, step=50.0)

bf_presenter.set_widgets(freq=freq_slider)

#%%
# To handle interaction, we will use the Bokeh `curdoc()` function to add the layout to the current 
# document, which allows for interaction with the widgets and the figure in a web browser.
# 

from bokeh.layouts import column, row # noqa: E402
from bokeh.io import curdoc # noqa: E402

widget_layout = column(freq_slider, grid_grid)
layout = row(widget_layout, source_plot)
curdoc().add_root(layout)


