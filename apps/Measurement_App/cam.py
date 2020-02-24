# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------

from numpy import uint32, empty, uint8
import cv2
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import CheckboxGroup

checkbox_use_camera = CheckboxGroup(labels=["use camera"], active=[])

cameraCDS = ColumnDataSource({'image_data':[]})

camWidgets = [checkbox_use_camera]

(M,N) = (120,160)
vc = cv2.VideoCapture(0)
vc.set(3,N)
vc.set(4,M)
img = empty((M, N), dtype=uint32)
view = img.view(dtype=uint8).reshape((M, N, 4))[::-1,::-1]
view[:,:,3] = 255

def update_camera():
    rval, frame = vc.read()
    if rval:
#        M, N, _ = frame.shape
        view[:,:,:3] = frame[:,:,:3] # copy red channel
#        view[:,:,1] = frame[:,:,1] # copy blue channel
#        view[:,:,2] = frame[:,:,2] # copy green channel
        cameraCDS.data['image_data'] = [img]