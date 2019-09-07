#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 18:33:00 2019

@author: kujawski
"""

from spectacoular import TimeSamples, MicGeom, PowerSpectra

file = "/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/examples/three_sources.h5"
file2 = "/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/examples/example_data.h5"
mgfile = "/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/acoular/xml/array_64.xml"

ts =TimeSamples(name=file)
mg = MicGeom()
ps = PowerSpectra(time_data=ts)


tsWidgets = ts.create_widgets_from_traits()
mgWidgets = mg.create_widgets_from_traits()
psWidgets = ps.create_widgets_from_traits()

# print values to check listeners 
[print(wd.value) for wd in tsWidgets]
[print(wd.value) for wd in mgWidgets]

ts.name = file2
mg.from_file = mgfile
[print(wd.value) for wd in tsWidgets]
[print(wd.value) for wd in mgWidgets]

psWidgets[0].value = '128'
print(ps.block_size)

#tsWidgets[0].value = file
#print(ts.name)
#
#invalidChannelWidget = mgWidgets[1]
