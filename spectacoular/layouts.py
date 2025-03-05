"""
Ready to use layout components that provide a high-level way to visualize and interact with Acoular.
"""
import acoular as ac
from pathlib import Path
import bokeh
from bokeh.plotting import figure
from traits.api import Instance, observe, Property, Bool, cached_property,\
    Dict, Int, Float
from .dprocess import MicGeomPresenter
from .factory import get_widgets, BaseSpectacoular
import numpy as np

def get_mic_files():
    """
    Get a list of all available microphone geometry files.
    """
    return [str(file) for file in (Path(ac.__file__).parent / 'xml').glob('*')]



class MicGeomComponent(BaseSpectacoular):

    presenter = Instance(MicGeomPresenter)

    figure = Instance(figure)

    # defaults to scatter
    glyph = Instance(bokeh.models.glyphs.Scatter, kw={
        'marker': 'circle_cross',
        'x': 'x',
        'y': 'y',
        'size': 20,
        'fill_alpha': 'alpha',
    })

    widgets = Property()

    allow_point_draw = Bool(False)

    mirror_view = Bool(False)

    mic_size = Int(10)

    mic_alpha = Float(0.8)

    #: dictionary containing the mapping between a class trait attribute and 
    #: a Bokeh widget. Keys: name of the trait attribute. Values: Bokeh widget.
    trait_widget_mapper = Dict({
        'mirror_view': bokeh.models.widgets.Toggle,
        'mic_size': bokeh.models.widgets.Slider
                       })

    #: dictionary containing arguments that belongs to a widget that is created
    #: from a trait attribute and should be considered when the widget is built.
    #: For example: {"traitname":{'disabled':True,'background_color':'red',...}}.
    trait_widget_args = Dict({
        'mirror_view': {"label": "Mirror X-Axis", "active": False},
        'mic_size': {"title": "Mic Size", "start": 0, "end": 50}
                     })

    #: dictionary containing the mapping between a class trait attribute and 
    #: a Bokeh widget for the microphone geometry object.
    mics_trait_widget_mapper = Dict(
        {'file': bokeh.models.widgets.Select}
    )

    #: dictionary containing arguments that belongs to a widget that is created
    #: from a trait attribute and should be considered when the widget is built.
    mics_trait_widget_args = Dict(
        {'file': {'title': 'Geometry File', 'value': get_mic_files()[0], 
        'options': get_mic_files()},
        }
    )

    _glyph_renderer = Instance(bokeh.models.renderers.GlyphRenderer)

    def _mirror_x_axis(self, event):
        """Flips the x-axis view of the scatter plot when the button is toggled."""
        if self.figure:
            current_start, current_end = self.figure.x_range.start, self.figure.x_range.end
            self.figure.x_range.start, self.figure.x_range.end = current_end, current_start

    def update_mic_size(self, attr, old, new):
        if type(self.glyph.size) is not str: # if size is a string, it is a reference to a column in the data source
            self.glyph.size = self.mic_size
        self.presenter.cdsource.data['sizes'] = np.ones(
            self.presenter.source.mpos_tot.shape[1]) * self.mic_size

    @observe('figure')
    def _remove_logo(self, event):
        self.figure.toolbar.logo = None

    @observe('presenter.cdsource, figure')
    def _add_glyph(self, event):
        if hasattr(self.presenter, 'cdsource') and self.figure:
            # Remove previous glyph if it exists
            if self._glyph_renderer in self.figure.renderers:
                self.figure.renderers.remove(self._glyph_renderer)
            self._glyph_renderer = self.figure.add_glyph(
                self.presenter.cdsource, self.glyph)

    @observe('figure, _glyph_renderer, allow_point_draw')
    def _add_point_draw(self, event):
        existing_tools = [tool for tool in self.figure.tools if isinstance(tool, bokeh.models.PointDrawTool)]
        for tool in existing_tools:
            self.figure.tools.remove(tool)

        if self.allow_point_draw and self._glyph_renderer is not None:
            draw_tool = bokeh.models.PointDrawTool(
                renderers=[self._glyph_renderer], empty_value=0.)
            self.figure.add_tools(draw_tool)
            self.figure.toolbar.active_tap = draw_tool

    def _add_invalid_channel_callback(self, widget):
        def _update_invalid_channels():
            nmics = self.presenter.source.mpos_tot.shape[1]
            inv = self.presenter.source.invalid_channels
            alpha = self.mic_alpha*np.ones(nmics)
            alpha[inv] = 0
            widget.options = [str(i) for i in range(nmics)]
            widget.value = [str(i) for i in inv]
            self.presenter.cdsource.data['alpha'] = alpha
        _update_invalid_channels()
        if self.presenter is not None:
            self.presenter.source.on_trait_change(_update_invalid_channels, 'digest')

    @cached_property
    def _get_widgets(self):
        # component widgets
        widgets = []
        cwidgets = self.get_widgets()
        if 'mirror_view' in cwidgets.keys():
            cwidgets['mirror_view'].on_click(self._mirror_x_axis)
        if 'mic_size' in cwidgets.keys():
            cwidgets['mic_size'].on_change('value', self.update_mic_size)
        
        if self.presenter is not None:
            if not hasattr(self.presenter.source, 'get_widgets'):
                if 'pos_total' in self.mics_trait_widget_mapper.keys():
                    if (self.mics_trait_widget_args.get('pos_total') is None) or self.mics_trait_widget_args['pos_total'].get('source') is not None:
                        self.mics_trait_widget_args['pos_total'].update({'source': self.presenter.cdsource})
                widgets = get_widgets(self.presenter.source, self.mics_trait_widget_mapper, self.mics_trait_widget_args)
            else:
                # update widget mapper
                self.presenter.source.trait_widget_mapper.update(self.mics_trait_widget_mapper)
                self.presenter.source.trait_widget_args.update(self.mics_trait_widget_args)
                if 'pos_total' in self.presenter.source.trait_widget_mapper.keys():
                    if (self.presenter.source.trait_widget_args.get('pos_total') is None) or self.presenter.source.trait_widget_args['pos_total'].get('source') is None:
                        self.presenter.source.trait_widget_args['pos_total'].update({'source': self.presenter.cdsource})
                widgets = self.presenter.source.get_widgets()
        if widgets.get('invalid_channels'):
            self._add_invalid_channel_callback(widgets['invalid_channels'])
        cwidgets.update(widgets)
        if widgets.get('file'):
            widgets['file'].on_change('value', self.update_mic_size)
        return cwidgets
