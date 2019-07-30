#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 15 16:21:22 2019

@author: kujawski
"""

import sys 
import os
from SamplesProcessor import TimeSamplesPhantom
from acoular import MicGeom, WNoiseGenerator, PointSource,\
 Mixer, WriteH5, TimeSamples, PowerSpectra, RectGrid, SteeringVector,\
 BeamformerBase, L_p, UncorrelatedNoiseSource, \
 MovingPointSource, Trajectory, \
 BeamformerDamas,BeamformerDamasPlus
from numpy import arange, cos, sin, pi
APPFOLDER =os.path.dirname(os.path.abspath( __file__ ))

sys.path.insert(0,os.path.join(os.path.dirname(__file__),'../../'))
H5SAVEFILE = 'two_sources_one_moving_60s.h5'
H5PATH = os.path.join(APPFOLDER,"static/",H5SAVEFILE)
DEV_SERIAL_NUMBERS = {'tornado': ['10142', '10112', '10125', '10126'],
                        'typhoon': [
                                '10092','10095','10030','10038',
                                '10115','10116','10118','10119',
                                '10120','10123',
                                ]}

def get_interface(device,syncorder=[]):
    if device == 'uma16':
        from acuma16 import UMA16SamplesGenerator
        InputSignalGen = UMA16SamplesGenerator()
        return InputSignalGen
    
    elif device == 'tornado' or device == 'typhoon':
        from sinus import SINUSDeviceManager, SINUSAnalogInputManager, \
        SINUSSamplesGenerator, ini_import
        
        if syncorder: 
            DevManager = SINUSDeviceManager(orderdevices = syncorder)
        elif not syncorder:
            DevManager = SINUSDeviceManager(orderdevices = DEV_SERIAL_NUMBERS[device])
            
        DevInputManager = SINUSAnalogInputManager()
        InputSignalGen = SINUSSamplesGenerator(manager=DevInputManager,
                                               inchannels=DevInputManager.namechannels)
        IniManager = ini_import()
        return IniManager, DevManager,DevInputManager,InputSignalGen
    
    elif device == 'phantom':
        print(os.path.dirname(os.path.abspath(__file__)))
        exist = os.path.isfile(H5PATH)
        if not exist:
            print("need to create three sources file first...")
            create_three_sources_moving()
        InputSignalGen = TimeSamplesPhantom(name=H5PATH)
        return InputSignalGen

def create_three_sources_moving():
    sfreq = 51200 
    duration = 60
    nsamples = duration*sfreq
    micgeofile = "Measurement_App/micgeom/array_64.xml"
    mg = MicGeom( from_file=micgeofile )
    n1 = WNoiseGenerator( sample_freq=sfreq, numsamples=nsamples, seed=100 )
    n2 = WNoiseGenerator( sample_freq=sfreq, numsamples=nsamples, seed=200, rms=0.7 )
    n3 = WNoiseGenerator( sample_freq=sfreq, numsamples=nsamples, seed=300, rms=0.5 )
    
    # trajectory of source
    tr = Trajectory()
    rps = 0.2 # revs pre second
    
    delta_t = 1./abs(rps)/16.0 # ca. 16 spline nodes per revolution 
    r1 = 0.141
    for t in arange(0, duration*1.001, delta_t):
        phi = t * rps * 2 * pi #angle
        # define points for trajectory spline
        tr.points[t] = (r1*cos(phi), r1*sin(phi), 0.3)

    # point sources
    p1 = MovingPointSource(signal=n1, mics=mg, trajectory=tr)

    p2 = PointSource( signal=n2, mics=mg,  loc=(0.15,0,0.3) )
    p3 = PointSource( signal=n3, mics=mg,  loc=(0,0.1,0.3) )
    pa = Mixer( source=p1, sources=[p2,p3] )
    wh5 = WriteH5( source=pa, name=H5PATH )
    wh5.save()

def create_three_sources():
    sfreq = 51200 
    duration = 60
    nsamples = duration*sfreq
    micgeofile = "Measurement_App/micgeom/array_64.xml"
    mg = MicGeom( from_file=micgeofile )
    n1 = WNoiseGenerator( sample_freq=sfreq, numsamples=nsamples, seed=100 )
    n2 = WNoiseGenerator( sample_freq=sfreq, numsamples=nsamples, seed=200, rms=0.7 )
    n3 = WNoiseGenerator( sample_freq=sfreq, numsamples=nsamples, seed=300, rms=0.5 )
    p1 = PointSource( signal=n1, mics=mg,  loc=(-0.1,-0.1,0.3) )
    p2 = PointSource( signal=n2, mics=mg,  loc=(0.15,0,0.3) )
    p3 = PointSource( signal=n3, mics=mg,  loc=(0,0.1,0.3) )
    pa = Mixer( source=p1, sources=[p2,p3] )
    wh5 = WriteH5( source=pa, name=H5PATH )
    wh5.save()
        
