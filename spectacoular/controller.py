# -*- coding: utf-8 -*-
#pylint: disable-msg=E0611, E1101, C0103, R0901, R0902, R0903, R0904, W0232
#------------------------------------------------------------------------------
# Copyright (c) 2020-2021, Acoular Development Team.
#------------------------------------------------------------------------------
"""Implements controller classes and functions """



def set_calc_button_callback(calcFunc, calcButton):
    """
    Sets a simple wrapper function to set a Bokeh button inactive and change 
    its label during calculation.
    
    
    Parameters
    ----------
    calcFunc : callable
        A callable function that sould be executed when calcButton is active.
    calcButton : bokeh.models.widgets.buttons.Toggle
        The Button, executing the calcFunc function.

    Returns
    -------
    None.

    """
    def calc(arg):
        calclabel = 'Calculating ...'
        if arg:
            calcButton.label = calclabel
            calcButton.disabled = True
            while not calcButton.label == calclabel and not calcButton.disabled:
                pass
            try:
                calcFunc()
            except Exception as ex:
                print(ex)
            calcButton.active = False
            calcButton.disabled = False
            calcButton.label = 'Calculate'
        else:
            calcButton.label = 'Calculate'
    calcButton.on_click(calc)


