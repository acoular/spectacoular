Install SpectAcoular
====================

Tools
-----
There are many different tools for Python environment management and package installation.
Select your preferred method by clicking on one of the tabs below.

.. include:: tools.rst

Virtual environment
-------------------
We strongly encourage the use of virtual environments. An environment ``my-env`` can be created with:

.. tab-set::
    :sync-group: tool

    .. tab-item:: ``uv``
        :sync: uv

        .. code-block:: console

            $ uv venv

        .. note::
           ``uv`` will handle environment activation implicitly (the environment is created at ``.venv``).

    .. tab-item:: ``venv``
        :sync: pip

        .. code-block:: console

            $ python3 -m venv my-env

        and activate the environment with:

        .. code-block:: console

            $ source my-env/bin/activate

Installation
------------
To install SpectAcoular, run the following in your terminal or command prompt:

.. tab-set::
    :sync-group: tool

    .. tab-item:: ``uv``
        :sync: uv

        .. code-block:: console

            $ uv pip install spectacoular

    .. tab-item:: ``pip``
        :sync: pip

        .. code-block:: console

            $ pip install -U spectacoular

Dependencies
------------
SpectAcoular depends on the following packages, which will be installed automatically unless they are already present:

============================================= ========
Package                                       Function
============================================= ========
`Acoular <https://acoular.org/>`_             Acoustic beamforming and signal processing.
`Bokeh <https://docs.bokeh.org/en/latest/>`_  Interactive plotting and browser-based user interfaces.
============================================= ========

Optional dependencies
^^^^^^^^^^^^^^^^^^^^^
Optional dependencies are only required for some applications and features, mainly the measurement and live-audio apps.

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Package
     - Needed for
   * - `opencv-python <https://opencv.org/>`_
     - Camera/image functionality in the measurement app.
   * - `sounddevice <https://python-sounddevice.readthedocs.io/>`_
     - Audio input via PortAudio-based hardware.

When installing SpectAcoular from PyPI, SpectAcoular and all optional dependencies can be installed with the ``full`` extra:

.. tab-set::
    :sync-group: tool

    .. tab-item:: ``uv``
        :sync: uv

        .. code-block:: console

            $ uv pip install 'spectacoular[full]'

    .. tab-item:: ``pip``
        :sync: pip

        .. code-block:: console

            $ pip install -U 'spectacoular[full]'

Verify your installation
------------------------
After installation, you can verify that SpectAcoular is working by starting one of the included applications:

.. tab-set::
    :sync-group: tool

    .. tab-item:: ``uv``
        :sync: uv

        .. code-block:: console

            $ uv run micgeom_app --show

    .. tab-item:: ``pip``
        :sync: pip

        .. code-block:: console

            $ micgeom_app --show

This should open a new browser window or tab with the microphone geometry application.

Known issues
------------

Missing PortAudio on Linux
^^^^^^^^^^^^^^^^^^^^^^^^^^
Live-audio features depend on ``sounddevice``, which in turn requires the system library PortAudio. When installing SpectAcoular with ``pip`` or ``uv`` on Linux, PortAudio might not be present yet.

On Ubuntu or Debian, you can install it with:

.. code-block:: console

    $ sudo apt install libportaudio2

This is only needed for applications that use live audio input, such as the level meter or measurement app.
