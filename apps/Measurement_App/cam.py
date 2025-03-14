#------------------------------------------------------------------------------
# Copyright (c) 2007-2020, Acoular Development Team.
#------------------------------------------------------------------------------

try:
    import cv2
    HAVE_CV2 = True
except ImportError:
    HAVE_CV2 = False

from functools import partial

import bokeh
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from numpy import empty, uint8, uint32
from traits.api import (
    Bool,
    Dict,
    Enum,
    Float,
    Instance,
    Int,
    Property,
    cached_property,
    observe,
)

from spectacoular import BaseSpectacoular

XCAM = (-0.5,-0.375,1.,0.75)

class CameraComponent(BaseSpectacoular):

    doc = Instance(bokeh.document.Document)
    active = Bool(False, desc="Whether to use the camera")
    image_type = Enum('Stream', 'Snapshot', desc="Type of image to display")
    camera_index = Int(0, desc="Index of the camera to use")
    framerate = Float(25, desc="framerate in frames/s")
    width = Int(640, desc="width of the camera image in pixels")
    height = Int(480, desc="height of the camera image in pixels")
    extent_x = Float(XCAM[0], desc="x-coordinate of the lower left corner of the camera image")
    extent_y = Float(XCAM[1], desc="y-coordinate of the lower left corner of the camera image")
    extent_width = Float(XCAM[2], desc="width of the camera image")
    extent_height = Float(XCAM[3], desc="height of the camera image")
    alpha = Float(1.0, desc="the alpha value of the image")

    figure = Instance(figure)

    glyph = Instance(bokeh.models.glyphs.ImageRGBA, kw={
        'image': 'image_data',
        'x': XCAM[0], 'y': XCAM[1], 'dw': XCAM[2], 'dh': XCAM[3],
    })

    trait_widget_mapper = Dict({
        'active': bokeh.models.widgets.Toggle,
        'image_type': bokeh.models.widgets.Select,
        'camera_index': bokeh.models.widgets.NumericInput,
        'framerate': bokeh.models.widgets.NumericInput,
        'width': bokeh.models.widgets.NumericInput,
        'height': bokeh.models.widgets.NumericInput,
        'extent_x': bokeh.models.widgets.NumericInput,
        'extent_y': bokeh.models.widgets.NumericInput,
        'extent_width': bokeh.models.widgets.NumericInput,
        'extent_height': bokeh.models.widgets.NumericInput,
        'alpha': bokeh.models.widgets.Slider,
    })

    trait_widget_args = Dict({
        'active': {"label": "Display", "active": False, "disabled": not HAVE_CV2, "button_type":"success"},
        'image_type': {"title": "Image Type", "options": ['Stream', 'Snapshot'], "disabled": not HAVE_CV2},
        'framerate' : {'mode': 'float', "disabled": True},
        'camera_index': {"title": "Camera Index", "value": 0, "disabled": not HAVE_CV2},
        'width': {"title": "Width", "value": 640, "disabled": True},
        'height': {"title": "Height", "value": 480, "disabled": True},
        'extent_x': {"title": "Lower Left X", "value": XCAM[0], "mode": "float", "disabled": not HAVE_CV2},
        'extent_y': {"title": "Lower Left Y", "value": XCAM[1], "mode": "float", "disabled": not HAVE_CV2},
        'extent_width': {"title": "Width", "value": XCAM[2], "mode": "float", "disabled": not HAVE_CV2},
        'extent_height': {"title": "Height", "value": XCAM[3], "mode": "float", "disabled": not HAVE_CV2},
        'alpha': {"title": "Image Alpha", 'start':0, 'end':1, 'step':0.05},
    })

    widgets = Property()

    # private traits
    _glyph_renderer = Instance(bokeh.models.renderers.GlyphRenderer)
    _callback_id = None
    _vc_stream = None

    @observe('figure')
    def _add_glyph(self, event):
        if self.figure:
            # Remove previous glyph if it exists
            if self._glyph_renderer in self.figure.renderers:
                self.figure.renderers.remove(self._glyph_renderer)
            self._glyph_renderer = self.figure.add_glyph(
                ColumnDataSource({'image_data': []}), self.glyph)

    def _update_camera(self, cds, img, view):
        rval, frame = self._vc_stream.read()
        if rval:
            view[:,:,0] = frame[:,:,2] # copy red channel
            view[:,:,2] = frame[:,:,0] # copy blue channel
            view[:,:,1] = frame[:,:,1] # copy green channel
            view[:,:,3] = int(255*self.alpha)# current alpha value
            cds.data['image_data'] = [img]

    def _camera_index_callback(self, attr, old, new):
        vc = cv2.VideoCapture(new)
        self.framerate = vc.get(cv2.CAP_PROP_FPS)
        self.width =  int(vc.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
        vc.release()

    def _camera_callback(self, attr, old, new, cds):
        if new:
            self._vc_stream = cv2.VideoCapture(self.camera_index)
            update_rate = 1000/self.framerate # in milliseconds
            update_rate = 2*update_rate # update only half as often as the camera
            M, N = self.height, self.width
            self._vc_stream.set(3, N)
            self._vc_stream.set(4, M)
            self._vc_stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Keep only the latest frame in buffer
            img = empty((M, N), dtype=uint32)
            view = img.view(dtype=uint8).reshape((M, N, 4))[::-1,::-1]
            view[:,:,3] = 255
            callback = partial(self._update_camera, cds=cds, img=img, view=view)
            if self.image_type == 'Stream':
                self._callback_id = self.doc.add_periodic_callback(callback, update_rate)
            else:
                self._callback_id = self.doc.add_next_tick_callback(callback)
        else:
            self._vc_stream.release()
            if self.image_type == 'Stream':
                self.doc.remove_periodic_callback(self._callback_id)
            cds.data['image_data'] = []  

    def _global_alpha_callback(self, attr, old, new):
        # go through all image glyphs and change global alpha if above
        for renderer in self.figure.renderers:
            if renderer is not self._glyph_renderer:
                if hasattr(renderer, 'global_alpha') and renderer.global_alpha > new:
                    renderer.global_alpha = new

    @cached_property
    def _get_widgets(self):
        widgets = self.get_widgets()
        if widgets.get('camera_index') is not None:
            widgets['camera_index'].on_change('value', self._camera_index_callback)
        if widgets.get('active') is not None:
            callback = partial(self._camera_callback, cds=self._glyph_renderer.data_source)
            widgets['active'].on_change('active', callback)
        return widgets

