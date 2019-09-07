#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 18:03:37 2019

@author: kujawski
"""

from bokeh.models import ColumnDataSource
from traits.api import Trait
import numpy as np

# =============================================================================
# TimeSamples class
# =============================================================================

from acoular import TimeSamples

data = {'sample':[],'values':[]}

def _update_column_data_source(self):
    self.cdsource.data = {
            'sample' : list(np.arange(0,self.numsamples)),
            'values' : list(self.data[:,0])
            }
#self.cdsource.data = {
#        'sample' : [list(np.arange(0,self.numsamples)) for i in range(self.numchannels)],
#        'values' : [list(self.data[:,i]) for i in range(self.numchannels)]
#        }    
    
# add column data source to TimeSamples class    
TimeSamples.add_class_trait(
        'cdsource',Trait(ColumnDataSource(data=data))
        )

# add method to class
setattr(TimeSamples,"_update_column_data_source",_update_column_data_source)

# add function to listener listener dict (listens on changes of basename)
TimeSamples.__listener_traits__['_update_column_data_source'] = (
        'method', 
        {'pattern': 'basename', 'post_init': False, 'dispatch': 'same'}
        )


# =============================================================================
# MicGeom class
# =============================================================================

from acoular import MicGeom

data = {'x':[],'y':[], 'channels':[]}

def _update_column_data_source(self):
    if self.num_mics > 0:
        self.cdsource.data = {
                'x' : self.mpos[0,:],
                'y' : self.mpos[1,:],
                'channels' : [str(_) for _ in range(self.num_mics)],
                'sizes' : [1 for _ in range(self.num_mics)]
                }        
    else:
        self.cdsource.data = {'x':[],'y':[], 'channels':[]}
        
    
# add column data source to TimeSamples class    
MicGeom.add_class_trait(
        'cdsource',Trait(ColumnDataSource(data=data))
        )

# add method to class
setattr(MicGeom,"_update_column_data_source",_update_column_data_source)

# add function to listener listener dict (listens on changes of basename)
MicGeom.__listener_traits__['_update_column_data_source'] = (
        'method', 
        {'pattern': 'from_file', 'post_init': False, 'dispatch': 'same'}
        )
