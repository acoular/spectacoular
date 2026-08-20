:orphan:

Measurement App
===============

This application records multichannel audio, displays channel levels, and can
perform live beamforming. For demonstration, it starts with a simulated **Phantom** audio stream,
so it can be used without measurement hardware.

Start the app
-------------

The Measurement App needs ``opencv-python`` for camera functionality. This is installed by the ``full`` extra.
So ensure that it is available and run the app with your preferred environment manager:

.. tab-set::
    :sync-group: tool

    .. tab-item:: ``uv``
        :sync: uv

        .. code-block:: console

            $ uv run --extra full msm_app

    .. tab-item:: ``pip``
        :sync: pip

        .. code-block:: console

            $ msm_app

    .. tab-item:: ``mamba``
        :sync: mamba

        .. code-block:: console

            $ msm_app

    .. tab-item:: ``conda``
        :sync: conda

        .. code-block:: console

            $ msm_app

Selecting an audio stream
-------------------------

Use the **Audio stream** dropdown at the top of the app to select a backend.

* **Phantom** is the default backend. It provides a synthetic rotating source
  for demonstrating the application's display, recording, and beamforming
  features without measurement hardware.
* **Sound device** captures a live input through PortAudio via the optional
  ``sounddevice`` dependency.

Choose the desired input device, channel count, sampling frequency, and sample
format in the backend settings. Backend settings and the stream selector are disabled while a display,
measurement, or beamforming workflow is running. Stop that workflow to change the stream backend or settings.

.. admonition:: Info

   For custom audio-stream controllers, see :ref:`the B.Y.O.B. section
   <byob-audio-stream-controllers>`. They are discovered by every :class:`~spectacoular.base.AudioStreamApp` automatically.

.. figure:: measurementapp.mp4
    :align: center
    :width: 100%
    :figwidth: 100%
