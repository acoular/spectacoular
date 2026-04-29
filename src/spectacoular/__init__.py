# ------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
# ------------------------------------------------------------------------------

from importlib.util import find_spec
from .bokehview import (
    add_bokeh_attr,
    SampleSplitter,
    BeamformerBase,
    BeamformerFunctional,
    BeamformerCapon,
    BeamformerEig,
    BeamformerMusic,
    BeamformerDamas,
    BeamformerDamasPlus,
    BeamformerOrth,
    BeamformerCleansc,
    BeamformerClean,
    BeamformerCMF,
    BeamformerGIB,
    PointSpreadFunction,
    RectGrid,
    RectGrid3D,
    MicGeom,
    Calib,
    Environment,
    SteeringVector,
    PowerSpectra,
    TimeSamples,
    MaskedTimeSamples,
    PointSource,
    Average,
    FiltOctave,
    Trigger,
    AngleTracker,
    SpatialInterpolator,
    SpatialInterpolatorRotation,
    SpatialInterpolatorConstantRotation,
    WriteH5,
    MaskedTimeOut,
)
from .factory import (
    BaseSpectacoular,
    DataTableMapper,
    NumericInputMapper,
    SelectMapper,
    SliderMapper,
    TextInputMapper,
    ToggleMapper,
    get_widgets,
    set_widgets,
)
from .controller import set_calc_button_callback
from .dprocess import (
    BeamformerPresenter,
    MicGeomPresenter,
    PointSpreadFunctionPresenter,
    TimeSamplesPresenter,
)
from .lprocess import (
    CalibHelper,
    TimeOutPresenter,
    TimeSamplesPhantom,
)
from .consumer import TimeBandsConsumer, TimeConsumer
from .layouts import MicGeomComponent
from .version import __author__, __date__, __version__

__all__ = [
    # Acoular
    "AngleTracker",
    "Average",
    "BeamformerBase",
    "BeamformerCMF",
    "BeamformerCapon",
    "BeamformerClean",
    "BeamformerCleansc",
    "BeamformerDamas",
    "BeamformerDamasPlus",
    "BeamformerEig",
    "BeamformerFunctional",
    "BeamformerGIB",
    "BeamformerMusic",
    "BeamformerOrth",
    "Calib",
    "Environment",
    "FiltOctave",
    "MaskedTimeOut",
    "MaskedTimeSamples",
    "MicGeom",
    "PointSource",
    "PointSpreadFunction",
    "PowerSpectra",
    "RectGrid",
    "RectGrid3D",
    "SampleSplitter",
    "SpatialInterpolator",
    "SpatialInterpolatorConstantRotation",
    "SpatialInterpolatorRotation",
    "SteeringVector",
    "TimeSamples",
    "Trigger",
    "WriteH5",
    # SpectAcoular
    "BaseSpectacoular",
    "BeamformerPresenter",
    "CalibHelper",
    "DataTableMapper",
    "MicGeomComponent",
    "MicGeomPresenter",
    "NumericInputMapper",
    "PointSpreadFunctionPresenter",
    "SelectMapper",
    "SliderMapper",
    "TextInputMapper",
    "TimeBandsConsumer",
    "TimeConsumer",
    "TimeOutPresenter",
    "TimeSamplesPhantom",
    "TimeSamplesPresenter",
    "ToggleMapper",
    "add_bokeh_attr",
    "get_widgets",
    "set_calc_button_callback",
    "set_widgets",
]
if find_spec("sounddevice"):
    from .bokehview import SoundDeviceSamplesGenerator
    from .lprocess import TimeSamplesPlayback

    __all__ += [
        "SoundDeviceSamplesGenerator",
        "TimeSamplesPlayback",
    ]
