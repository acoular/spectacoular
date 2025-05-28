# ------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
# ------------------------------------------------------------------------------
"""
.. _basic_mic_geom_widgets:

Creating widgets with SpectAcoular
==================================

In this example, we are going to create an interactive plot of a Microphone Array Geometry with additional control widgets 
using the SpectAcoular package.


.. bokeh-plot:: ../examples/basic_mic_geom_widgets.py
   :source-position: none


"""
#%% 
# Set up the microphone geometry plot
# -----------------------------------
#
# Similar to the :ref:`basic_mic_geom_plot`, we will first import the necessary modules and set up 
# the microphone geometry plot.
 
import acoular as ac
import spectacoular as sp
from pathlib import Path
from bokeh.models import ColumnDataSource 
from bokeh.plotting import figure 

# set up the figure
figure = figure(title='Microphone Geometry', tools='hover,zoom_in,zoom_out,reset,lasso_select', match_aspect=True)

# set up the microphone geometry
default_xml_file = Path(ac.__file__).parent / 'xml' / 'tub_vogel64.xml'
mics = sp.MicGeom(file=default_xml_file)

# add circles to the figure to represent the microphones
cds = ColumnDataSource(data={'x': mics.pos_total[0], 'y': mics.pos_total[1]})
glyph = figure.circle(x='x', y='y', radius=0.02, line_color='black', fill_color='#1F77B4', fill_alpha=0.4, source=cds)

    
        
#%% 
# Create widgets for MicGeom
# --------------------------
#
# The :class:`~acoular.microphones.MicGeom` class provides several attributes, known as traits, that can be used to 
# either provide additional information about the microphone array or to modify the geometry.
#
print(mics.traits().keys())

# Out:
# ['num_mics', 'center', 'aperture', 'file', 'pos_total', 'pos',  ...]

#%%
# Let's say we want to know about the number of microphones (:attr:`~acoular.microphones.MicGeom.num_mics`) and 
# the aperture of the microphone array (:attr:`~acoular.microphones.MicGeom.aperture`), we can use SpectAcoular's 
# :func:`~spectacoular.factory.get_widgets` function to translate each attribute into a Bokeh widget.
# 
# Defining each trait to widget mapping individually can become cumbersome, and not all
# widgets are suitable for all traits. Therefore, SpectAcoular provides default widget mapping for 
# most of Acoular's classes.

from bokeh.models.widgets import NumericInput # noqa: E402

numeric_widgets = mics.get_widgets(
    {'aperture' : NumericInput, 'num_mics': NumericInput},
    {'aperture': {'title': 'Aperture/m', 'disabled': True},
     'num_mics': {'title': 'Number of Mics', 'disabled': True}})

#%% 
# It would also be beneficial to have a widget that allows the user to edit the microphone positions 
# and to display the coodinates in a table format. Both can be achieved by using Bokeh's 
# :class:`~bokeh.models.DataTable` widget. In addition, we will use the 
# :class:`~bokeh.models.NumberEditor` to allow the user to edit the values in the table.

from bokeh.models.widgets import DataTable # noqa: E402
from bokeh.models import TableColumn, NumberEditor # noqa: E402

editor = NumberEditor()
pos_table = [
    TableColumn(field='x', title='x/m', editor=editor),
    TableColumn(field='y', title='y/m', editor=editor),
    TableColumn(field='z', title='z/m', editor=editor)
        ]

# get the widgets for the MicGeom instance
data_table_widget = mics.get_widgets(
    {'pos_total': DataTable}, 
    {'pos_total': {'height': 450, 'transposed': True, 'columns': pos_table, 'source': cds, 'editable': True}}
    )

#%% 
# Finally, we want to allow the user to add or remove microphones from the microphone array.
# Therefore, we will use the :class:`~bokeh.models.tools.PointDrawTool`.

from bokeh.models import PointDrawTool # noqa: E402


draw_tool = PointDrawTool(renderers=[glyph], empty_value=0.)

figure.add_tools(draw_tool)
figure.toolbar.active_tap = draw_tool


#%%
# Let's create a layout that contains the figure and the widgets. 

from bokeh.layouts import column, row # noqa: E402
from bokeh.io import show # noqa: E402

widget_column = column(*numeric_widgets.values(), *data_table_widget.values(), width=400)
layout = row(figure, widget_column)
show(layout)  # Show the plot in a new browser window

#%% 
# The following code is for Bokeh server apps only.

from bokeh.io import curdoc
curdoc().add_root(layout)  # Add the layout to the current document for Bokeh server apps
