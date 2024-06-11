#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------

from numpy import uint32, empty, uint8
import cv2
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import CheckboxGroup

BFALPHA = 0.45

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
        view[:,:,0] = frame[:,:,2] # copy red channel
        view[:,:,2] = frame[:,:,0] # copy blue channel
        view[:,:,1] = frame[:,:,1] # copy green channel
        cameraCDS.data['image_data'] = [img]

def set_alpha_callback(bfImage):
    def global_alpha_callback(attr,old,new):
        if checkbox_use_camera.active: 
            bfImage.glyph.global_alpha = BFALPHA
        else:
            bfImage.glyph.global_alpha = 1
    checkbox_use_camera.on_change('active',global_alpha_callback)
        
def set_camera_callback(doc):
    def checkbox_use_camera_callback(attr,old,new):
        global periodic_plot_callback
        if checkbox_use_camera.active: 
            periodic_plot_callback = doc.add_periodic_callback(update_camera,40)
        else:
            doc.remove_periodic_callback(periodic_plot_callback)
            cameraCDS.data['image_data'] = []
    checkbox_use_camera.on_change('active',checkbox_use_camera_callback)