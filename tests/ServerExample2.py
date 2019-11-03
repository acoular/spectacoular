#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 17:45:33 2019
@author: kujawski
"""

from bokeh.layouts import column, row
from bokeh.models.widgets import Panel,Tabs,Div, Dropdown
from bokeh.plotting import figure
from bokeh.server.server import Server
from spectacoular import MaskedTimeSamples, MicGeom, PowerSpectra, \
RectGrid, SteeringVector, BeamformerBase, BeamformerView,TimeSamplesView


# build processing chain
ts = MaskedTimeSamples(name='/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/examples/example_data.h5')
mg = MicGeom(from_file='/home/kujawski/Dokumente/Code/acoular_workingcopy/acoular/acoular/xml/array_56.xml')
ps = PowerSpectra(time_data=ts)
rg = RectGrid(x_min=-0.6, x_max=-0.0, y_min=-0.3, y_max=0.3, z=0.68,increment=0.05)
st = SteeringVector( grid = rg, mics=mg )    
bb = BeamformerBase( freq_data=ps, steer=st )  


def create_content_handler(dic):
    menu = [(k,k) for k in dic.keys()]
    dropdown = Dropdown(label="Select", button_type="warning", menu=menu)
    dropdownCol=column(dropdown,column(*dic[list(dic.keys())[0]]))    
    def change_content(attr,old,new):
        print(new)
        dropdownCol.children[-1] = column(*dic[new])        
    dropdown.on_change('value',change_content)
    return dropdownCol 
      
def server_doc(doc):
    
    # get widgets to control settings
    tsWidgets = ts.get_widgets()
    mgWidgets = mg.get_widgets()
    bbWidgets = bb.get_widgets()

    dic = {"TimeSamples":tsWidgets,
           "MicGeom":mgWidgets,
       "Beamformer":bbWidgets}
    
    dropdownCol = create_content_handler(dic)    


    ### CREATE LAYOUT ### 
    
    # Tabs
    tsTab = Panel(child=dropdownCol,title='Time Signal')
    ControlTabs = Tabs(tabs=[tsTab],width=850)

    # make Document
    doc.add_root(ControlTabs)

# Setting num_procs here means we can't touch the IOLoop before now, we must
# let Server handle that. If you need to explicitly handle IOLoops then you
# will need to use the lower level BaseServer class.
server = Server({'/': server_doc}, num_procs=1)
server.start()


if __name__ == '__main__':
    print('Opening Bokeh application on http://localhost:5006/')

    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()

