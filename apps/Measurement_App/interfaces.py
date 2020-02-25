# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------
import sys 
import os
from spectacoular import TimeSamplesPhantom
from acoular import MicGeom, WNoiseGenerator, PointSource,\
Mixer, WriteH5, MovingPointSource, Trajectory
from numpy import arange, cos, sin, pi

APPFOLDER =os.path.dirname(os.path.abspath( __file__ ))

sys.path.insert(0,os.path.join(os.path.dirname(__file__),'../../'))
H5SAVEFILE = 'two_sources_one_moving_10s.h5'
H5PATH = os.path.join(APPFOLDER,"static/",H5SAVEFILE)

def get_interface(device,syncorder=[]):
    if device == 'uma16':
        from acuma16 import UMA16SamplesGenerator
        InputSignalGen = UMA16SamplesGenerator()
        return InputSignalGen
    elif device == 'phantom':
        exist = os.path.isfile(H5PATH)
        if not exist:
            print("need to create three sources file first...")
            create_three_sources_moving()
        InputSignalGen = TimeSamplesPhantom(name=H5PATH)
        return InputSignalGen

def create_three_sources_moving():
    sfreq = 51200 
    duration = 10
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
    duration = 10
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
        
