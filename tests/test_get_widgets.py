# ------------------------------------------------------------------------------
# Copyright (c) Acoular Development Team.
# ------------------------------------------------------------------------------
"""Tests for widget generation on SpectAcoular-exposed classes."""

import importlib
import inspect
import pkgutil

import spectacoular as sp

import pytest
from traits.api import HasTraits


def get_all_classes(*, hastraits_only=False, module='acoular'):
    """Collect classes from a package and, optionally, only ``HasTraits`` subclasses."""
    classes = []
    package = importlib.import_module(module)
    for module_info in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
        if module_info.name.endswith('traitsviews'):
            continue
        if '.apps.' in module_info.name:
            continue
        module = importlib.import_module(module_info.name)
        # skip traitsviews module
        for _, cls in inspect.getmembers(module, inspect.isclass):
            # ensure class is defined in the current module
            if cls.__module__ == module_info.name and (not hastraits_only or issubclass(cls, HasTraits)):
                classes.append(cls)
    return classes


acoular_classes = get_all_classes()
spectacoular_classes = get_all_classes(hastraits_only=True, module='spectacoular')
spectacoular_class_names = [cls.__name__ for cls in spectacoular_classes]


@pytest.mark.skip(reason='Not all Acoular classes have a validated SpectAcoular view yet.')
@pytest.mark.parametrize('cls', acoular_classes)
def test_view_exists(cls):
    """Check that an Acoular class is exposed with widget metadata in SpectAcoular."""
    if inspect.isabstract(cls):
        pytest.skip(f'{cls} is an abstract base class.')
    sp_cls = getattr(sp, cls.__name__, None)
    if sp_cls is None:
        pytest.fail(f'{cls.__name__} is not exposed by SpectAcoular.')
    if not hasattr(sp_cls, 'get_widgets'):
        pytest.fail(f'{cls.__name__} does not define get_widgets.')
    if not hasattr(sp_cls, 'trait_widget_mapper'):
        pytest.fail(f'{cls.__name__} does not define trait_widget_mapper.')


@pytest.mark.parametrize('cls', acoular_classes)
def test_get_widgets(cls):
    """Test that ``get_widgets`` can be called."""
    if inspect.isabstract(cls):
        pytest.skip(f'{cls} is an abstract base class.')
    # Test whether the class is exposed by SpectAcoular and provides widget mappings.
    sp_cls = getattr(sp, cls.__name__, None)
    if sp_cls is None:
        pytest.skip(f'{cls} is not implemented in SpectAcoular.')
    if not hasattr(sp_cls, 'get_widgets'):
        pytest.skip(f'{cls} does not have get_widgets method.')

    if cls.__name__ == 'SoundDeviceSamplesGenerator':
        sd = importlib.import_module('sounddevice')
        # In some cases, the default value ``device=0`` is invalid.
        # Use the default input device instead.
        device = sd.default.device[0]
        try:
            sd.query_devices(device)
            sp_instance = sp_cls(device=device)
        except sd.PortAudioError as e:
            pytest.skip(f'{cls} cannot be tested with device={device}. {e}')
    else:
        # test default
        sp_instance = sp_cls()
    widgets_default = sp_instance.get_widgets()
    if len(widgets_default) == 0:
        pytest.fail(f'get_widgets returned an empty dict for {cls.__name__} with default mapping')

    # now test each default mapping individually
    for key, value in sp_instance.trait_widget_mapper.items():
        arg = sp_instance.trait_widget_args.get(key)
        if arg:
            sp_instance.get_widgets({key: value}, {key: arg})
        else:
            sp_instance.get_widgets({key: value})
