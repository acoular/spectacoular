Installing SpectAcoular
========================

Requirements
------------

SpectAcoular requires Python 3 and runs on all major platforms. A working Python environment with the following packages is required:

**Required dependencies** (installed automatically):
  - `Acoular <http://www.acoular.org/>`_ 
  - `Bokeh <https://docs.bokeh.org/en/latest/>`_ 

**Optional dependencies** (for certain applications):
  - `OpenCV <https://opencv.org/>`_ 
  - `Sounddevice <https://python-sounddevice.readthedocs.io/en/0.4.1/>`_ 

.. note::

   If using `pip` to install `sounddevice`, make sure the **PortAudio library** is installed on your system. Alternatively, using `conda` is recommended for handling this dependency, as it includes PortAudio.

Installation with pip
---------------------

To install SpectAcoular using `pip`, run the following in your terminal or command prompt:

.. code-block:: console

    pip install spectacoular

To install the optional dependencies for all apps (e.g., `opencv-python` and `sounddevice`), use the `full` install option:

.. code-block:: console

    pip install spectacoular[full]

Installation with conda, micromamba, or mamba
---------------------------------------------

If you use the `conda`, `mamba`, or `micromamba` package manager, you can install SpectAcoular from the `acoular` channel:

.. code-block:: console

    conda install -c acoular spectacoular

This installs the core SpectAcoular package and its required dependencies. However, note that `conda` **does not support** the `spectacoular[full]` extras syntax. To install optional dependencies like `opencv` and `sounddevice` via `conda`, use:

.. code-block:: console

    conda install -c conda-forge opencv sounddevice

This approach ensures that `sounddevice` works correctly, as the required system library (PortAudio) is included.

