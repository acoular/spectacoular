Audio-stream controllers
========================

Any SpectAcoular application based on
:class:`~spectacoular.apps.base.AudioStreamApp` discovers audio-stream
controllers through the ``spectacoular.audio_stream_controls`` entry-point
group. A controller provides an Acoular-compatible source and optional Bokeh
configuration widgets for the backend audio stream.

.. _byob-audio-stream-controllers:

B.Y.O.B. - Bring your own backend
---------------------------------

Built-in controllers are **Phantom**, a simulated stream, and **Sound device**,
which captures live audio through PortAudio. In your own Python package, you
can define a custom audio stream backend by subclassing
:class:`~spectacoular.apps.controls.BaseAudioStreamControl`. For example, this
controller makes a
custom :class:`~acoular.base.SamplesGenerator` available as **My recorder** in
every application's **Audio stream** dropdown:

.. code-block:: python

    from bokeh.models import Select
    from spectacoular.apps.controls import BaseAudioStreamControl
    from my_package import MyRecorder


    class MyRecorderControl(BaseAudioStreamControl):
        id = "my-recorder"
        label = "My recorder"

        def create_source(self):
            return MyRecorder(sample_freq=51200, num_channels=64)

        def __init__(self, doc, logger=None):
            super().__init__(doc, logger)
            self.mode = Select(title="Mode", value="normal", options=["normal", "quiet"])
            self.mode.on_change("value", self._mode_changed)

        def _mode_changed(self, _attr, _old, value):
            self.source.mode = value
            self.source_changed()

        def get_widgets(self):
            return self.widget_panel(self.mode)

        def set_config_enabled(self, enabled):
            self.mode.disabled = not enabled

The only thing you need to do is to declare it your package's ``pyproject.toml`` as a SpectAcoular audio stream
controller and it becomes an available backend, if your package is installed in the same virtual envrionment as
SpectAcoular:

.. code-block:: toml

    [project.entry-points."spectacoular.audio_stream_controls"]
    my-recorder = "my_package:MyRecorderControl"

``create_source`` must return a source accepted by the application's processing
pipeline, i.e., an Acoular :class:`~acoular.base.SamplesGenerator`. Call ``source_changed()`` after replacing the source or changing a
setting that requires its pipeline to be rebuilt. The application calls
``start()``, ``stop()``, and ``close()`` around active workflows; override them
when the backend owns acquisition resources.
