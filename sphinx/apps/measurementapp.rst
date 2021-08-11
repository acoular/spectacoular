Microphone Array Measurement App
================================

This application can be used to record audio signals from multiple input channels and to perform live beamforming. Channel levels are displayed in a bar graph. The App offers different operating modes. 

The 'phantom' mode serves as a demonstration of the application features. The 'uma16' mode runs the app as a measurement software interface with the `miniDSP UMA16 MEMS <https://www.minidsp.com/products/usb-audio-interface/uma-16-microphone-array>`_ microphone array as the measurement hardware.

Serving the Application in Phantom mode:
----------------------------------------

Navigate to the `spectacoular/apps` folder and type the following command in a dedicated console (e.g. shell)

.. code-block:: console

    $ bokeh serve --show  Measurement_App --args --device=phantom --blocksize=256
    
Alternatively one can start the shell script named `start_phantom.sh`


Serving the Application with an UMA16 microphone array:
-------------------------------------------------------

Navigate to the `spectacoular/apps` folder and type the following command in a dedicated console (e.g. shell)

.. code-block:: console

    $ bokeh serve --show Measurement_App --args --device=uma16 --blocksize=256
    
Alternatively one can start the shell script named `start_uma.sh`


Serving this application in phantom mode produces the following interactive interface in your browser:
   
.. figure:: measurementapp.mp4
    :align: center
    :width: 100%
    :figwidth: 100%


  

