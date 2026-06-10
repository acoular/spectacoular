# ------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
# ------------------------------------------------------------------------------
"""Implement controller classes and functions."""

from bokeh.models import CustomJS


def set_calc_button_callback(calc_func, calc_button, label='Calculate', active_label='Calculating ...'):
    """Set a Bokeh button inactive and change its label during calculation.

    Parameters
    ----------
    calc_func : callable
        Callable function that is executed when ``calc_button`` is active.
    calc_button : bokeh.models.widgets.buttons.Toggle
        Button executing ``calc_func``.
    label : str, optional
        Label of the button when it is inactive. The default is ``'Calculate'``.
    active_label : str, optional
        Label of the button when it is active. The default is
        ``'Calculating ...'``.

    Returns
    -------
    None.

    """
    js_callback = CustomJS(
        args={'label': label, 'active_label': active_label},
        code="""
    // Callback disabling the button.
    if (cb_obj.active) {
        cb_obj.label = active_label;
        cb_obj.disabled = true;
    } else {
        cb_obj.label = label;
        cb_obj.disabled = false;
    }
    """,
    )

    def calc(attr, old, new):
        del attr, old, new
        if calc_button.active:
            try:
                calc_func()
            finally:
                calc_button.active = False

    calc_button.js_on_change('active', js_callback)
    calc_button.on_change('active', calc)
