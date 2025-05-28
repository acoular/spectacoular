:orphan:

Microphone Array Measurement App
================================

This application can be used to record audio signals from multiple input channels and to perform live beamforming. Channel levels are displayed in a bar graph. The App offers different operating modes. 

The 'phantom' mode serves as a demonstration of the application features. The 'sounddevice' mode runs the app as a measurement software capturing the audio stream provided by the PortAudio library.

This allows to use USB interfaces such as the `miniDSP UMA16 MEMS <https://www.minidsp.com/products/usb-audio-interface/uma-16-microphone-array>`_ microphone array as the measurement hardware.

Note that the 'sounddevice' mode requires to install spectacoular with full dependencies. This can be done by running

.. code-block:: console

    $ conda install -c acoular spectacoular[full]

Serving the Application in Phantom mode:
----------------------------------------

One can run the application by simply running 

.. code-block:: console

    $ msm_app --show --args --device=phantom

in the command line or by navigating to the `spectacoular/apps` directory. Then, type the following command in a dedicated console (e.g. shell)

.. code-block:: console

    $ bokeh serve --show  Measurement_App --args --device=phantom --blocksize=256
    
Alternatively one can start the shell script named `start_phantom.sh`


Serving the Application with an UMA16 microphone array:
-------------------------------------------------------

Run the application with 

.. code-block:: console

    $ msm_app --show --args --device=sounddevice


Alternatively, navigate to the `spectacoular/apps` folder and type the following command in a dedicated console (e.g. shell)

.. code-block:: console

    $ bokeh serve --show Measurement_App --args --device=sounddevice --blocksize=256
    
Alternatively one can start the shell script named `start_sounddevice.sh`. In the browser window, one can now select the UMA16 as the input device (named as *nanoSHARC micArray16*).
For beamforming go to the *Microphone Geometry* tab and select the micrphone geometry *minidsp_uma16.xml*. Then, start the audio stream by pressing the *start display* button. Beamforming can be performed by pressing the *start beamforming* button.

Serving this application in phantom mode produces the following interactive interface in your browser:
   
.. figure:: measurementapp.mp4
    :align: center
    :width: 100%
    :figwidth: 100%


  

