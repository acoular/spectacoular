:orphan:

Microphone Array Measurement App
================================

This application can be used to record audio signals from multiple input channels and to perform live beamforming. Channel levels are displayed in a bar graph, and the app offers different operating modes.

The ``phantom`` mode serves as a demonstration of the application features. The ``sounddevice`` mode runs the app as measurement software capturing the audio stream provided by the PortAudio library.

This allows the use of USB interfaces such as the `miniDSP UMA16 MEMS <https://www.minidsp.com/products/usb-audio-interface/uma-16-microphone-array>`_ microphone array as measurement hardware.

The ``sounddevice`` mode requires SpectAcoular's optional dependencies. Install them with one of the following commands:

If you operate in an active environment:

.. code-block:: console

    $ pip install 'spectacoular[full]'

or, with ``uv``:

.. code-block:: console

    $ uv pip install 'spectacoular[full]'

Starting the application in phantom mode
----------------------------------------

If SpectAcoular is installed in an activated environment, run:

.. code-block:: console

    $ msm_app --device=phantom --blocksize=256

If you installed SpectAcoular with ``uv`` and did not activate the environment, run:

.. code-block:: console

    $ uv run msm_app --device=phantom --blocksize=256

Starting the application with an UMA16 microphone array
-------------------------------------------------------

If SpectAcoular is installed in an activated environment, run:

.. code-block:: console

    $ msm_app --device=sounddevice --blocksize=256

If you installed SpectAcoular with ``uv`` and did not activate the environment, run:

.. code-block:: console

    $ uv run msm_app --device=sounddevice --blocksize=256

In the browser window, you can now select the UMA16 as the input device (named *nanoSHARC micArray16*).
For beamforming, go to the *Microphone Geometry* tab and select the microphone geometry *minidsp_uma16.xml*. Then start the audio stream by pressing the *start display* button. Beamforming can be started by pressing the *start beamforming* button.

Starting this application in phantom mode produces the following interactive interface in your browser:

.. figure:: measurementapp.mp4
    :align: center
    :width: 100%
    :figwidth: 100%
