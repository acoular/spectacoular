#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 19 20:29:58 2020

@author: kujawski
"""

from acoular import TimeSamples, TimeAverage
from SamplesProcessor import CalibHelper


ts = TimeSamples()
ta = TimeAverage(source=ts,naverage=256)
ch = CalibHelper(source=ta)

ts.name='example_data.h5'

widgets = ch.get_widgets()

# gen = ch.result(2)

# data = next(gen)
