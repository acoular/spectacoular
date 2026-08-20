:orphan:

Microphone Array Measurement App
================================

This application records multichannel audio, displays channel levels, and can
perform live beamforming. For demonstration, it starts with a simulated **Phantom** audio stream,
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
The **Phantom** backend is the default. It simulates an
audio stream. **Sound device** captures a real audio input using the optional
``sounddevice`` dependency. Install it with:

.. code-block:: console

    $ pip install 'spectacoular[full]'

or:

.. code-block:: console

    $ uv pip install 'spectacoular[full]'

Choose the desired input device, channel count, sampling frequency, and sample
format in the backend settings. Backend settings and the stream selector are disabled while a display,
measurement, or beamforming workflow is running. Stop that workflow before
changing stream backend or settings.

The application uses its built-in processing defaults. Persistent configuration
is not yet provided.

Custom audio-stream controllers are documented in
:doc:`../user_guide/audio_stream_controls`. They are discovered by every
SpectAcoular application based on ``AudioStreamApp``.

.. figure:: measurementapp.mp4
    :align: center
    :width: 100%
    :figwidth: 100%
