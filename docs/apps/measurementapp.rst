:orphan:

Microphone Array Measurement App
================================

This application records multichannel audio, displays channel levels, and can
perform live beamforming. It starts with the bundled **Phantom** audio stream,
so it can be used without measurement hardware.

Start the app
-------------

If SpectAcoular is installed in an active environment, run:

.. code-block:: console

    $ msm_app

Or, without activating a ``uv`` environment:

.. code-block:: console

    $ uv run msm_app

Selecting an audio stream
-------------------------

Use the **Audio stream** dropdown at the top of the app to select a backend.
The **Phantom** backend is the default. It reads the bundled demonstration
audio stream. **Sound device** captures a live input using the optional
``sounddevice`` dependency. Install it with:

.. code-block:: console

    $ pip install 'spectacoular[full]'

or:

.. code-block:: console

    $ uv pip install 'spectacoular[full]'

Choose the desired input device and channel count in the backend settings.
Backend settings and the stream selector are disabled while a display,
measurement, or beamforming workflow is running. Stop that workflow before
changing stream backend or settings.

The application uses its built-in processing defaults. Persistent configuration
is not yet provided.

.. figure:: measurementapp.mp4
    :align: center
    :width: 100%
    :figwidth: 100%
