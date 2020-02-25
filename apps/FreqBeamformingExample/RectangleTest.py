#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 16:12:20 2020

@author: kujawski
"""

from bokeh.io import curdoc
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource
from bokeh.models.tools import BoxEditTool

cds = ColumnDataSource(data={'x':[],'y':[],'width':[], 'height':[]})

p = figure(x_range=(0, 10), y_range=(0, 10), width=400, height=400,tools='box_edit,box_select')
r1 = p.rect('x', 'y', 'width', 'height',color='red',alpha=.3, source=cds)
tool = BoxEditTool(renderers=[r1])
p.add_tools(tool)
cds.on_change('data',lambda attr,old,new: print(cds.data))
doc = curdoc()
doc.add_root(p)