#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 18:33:00 2019

@author: kujawski
"""

from spectacoular import TimeSamples, MicGeom, PowerSpectra, TimeSamplesPresenter,\
BeamformerBase, MicGeomPresenter

file = "/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/examples/three_sources.h5"
file2 = "/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/examples/example_data.h5"
mgfile = "/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/acoular/xml/array_64.xml"

# initialize classes
ts =TimeSamples(name=file)
ps = PowerSpectra(time_data=ts)

# create widget lists
tsWidgets = ts.get_widgets()
psWidgets = ps.get_widgets()

# print values to check listeners 
print([(wd.value) for wd in tsWidgets])
#[print(wd.value) for wd in mgWidgets]

ts.name = file2
print([(wd.value) for wd in tsWidgets])

psWidgets[0].value = '128'
print(ps.block_size)
ps.block_size = 1024
psWidgets[0].value
psWidgets[3].value = 'False'

#%%

bb = BeamformerBase()
bbWidgets = bb.get_widgets()

# %%
# micGeom

mg = MicGeom()
mgWidgets = mg.get_widgets()
print([(wd.value) for wd in mgWidgets])

mg.from_file = mgfile
print([(wd.value) for wd in mgWidgets])

# set invalid channels via widget
mg.invalid_channels = [0,1,2,3]
print([(wd.value) for wd in mgWidgets])
mgWidgets[1].value = ' 3,5,9'
print(mg.invalid_channels)
#[print(wd.value) for wd in mgWidgets]


#%%

tv = TimeSamplesPresenter(source=ts)
tv.selectChannel.value = ['1','2']

#%%

mg = MicGeom(from_file='/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/acoular/xml/array_56.xml')
mgp = MicGeomPresenter(source=mg)

mg.from_file = '/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/acoular/xml/array_64.xml'

