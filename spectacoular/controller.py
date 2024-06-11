#------------------------------------------------------------------------------
# Copyright (c), Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements controller classes and functions """

from bokeh.models import CustomJS


def set_calc_button_callback(calcFunc, calcButton, label='Calculate', active_label='Calculating ...'):
    """
    Sets a simple wrapper function to set a Bokeh button inactive and change 
    its label during calculation.
    
    
    Parameters
    ----------
    calcFunc : callable
        A callable function that sould be executed when calcButton is active.
    calcButton : bokeh.models.widgets.buttons.Toggle
        The Button, executing the calcFunc function.
    label : str, optional
        The label of the button when it is inactive. The default is 'Calculate'.
    active_label : str, optional
        The label of the button when it is active. The default is 'Calculating ...'.

    Returns
    -------
    None.

    """

    js_callback = CustomJS(args=dict(label=label, active_label=active_label), code="""

    // Callback disabeling the button

    if (cb_obj.active) {
        cb_obj.label = active_label;
        cb_obj.disabled = true;
    }
    else {
        cb_obj.label = label;
        cb_obj.disabled = false;
    }

    """)


    def calc(attr, old, new):
        if calcButton.active:
            try:
                calcFunc()
            except Exception as ex:
                print(ex)
            finally:
                calcButton.active = False
    calcButton.js_on_change('active', js_callback)
    calcButton.on_change('active', calc)


