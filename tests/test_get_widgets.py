# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2019, Acoular Development Team.
#------------------------------------------------------------------------------

from spectacoular import *

classes = (SampleSplitter, Calib, Environment,SteeringVector,BeamformerBase,
           BeamformerFunctional, BeamformerCapon, BeamformerEig, BeamformerMusic,
           BeamformerDamas, BeamformerDamasPlus,BeamformerOrth,BeamformerCleansc,
           BeamformerClean,BeamformerCMF,BeamformerGIB,PointSpreadFunction,
           RectGrid,RectGrid3D,MicGeom,PowerSpectra,TimeSamples,MaskedTimeSamples,
           PointSource,TimeAverage)

for c in classes:
    print(c)
    instance_ = c().get_widgets()
    